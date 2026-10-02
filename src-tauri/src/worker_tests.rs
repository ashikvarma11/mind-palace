use super::*;

// The planned desktop has one supervised worker. Real-process tests share
// that single-worker constraint; framing-only tests can still run in parallel.
#[cfg(windows)]
static PROCESS_TEST_LOCK: std::sync::Mutex<()> = std::sync::Mutex::new(());

#[test]
#[cfg(windows)]
fn synchronous_launch_control_probe() {
    let _single_worker = PROCESS_TEST_LOCK.lock().unwrap_or_else(|error| error.into_inner());
    use std::io::Write;
    use std::os::windows::process::CommandExt;
    let bundle = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("resources/memory-worker");
    let executable = verify_bundle(&bundle).unwrap();
    let temporary = std::env::temp_dir().join(format!("mp-rust-control-{}", uuid::Uuid::new_v4()));
    fs::create_dir(&temporary).unwrap();
    let mut command = std::process::Command::new(executable);
    command.args(["--mode", "ui", "--vault"]).arg(temporary.join("vault")).arg("--create-vault")
        .current_dir(&bundle).env_clear().creation_flags(0x08000000)
        .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::null());
    for name in ["SystemRoot", "WINDIR", "TEMP", "TMP"] {
        if let Some(value) = std::env::var_os(name) { command.env(name, value); }
    }
    command.env("PATH", PathBuf::from(std::env::var_os("SystemRoot").unwrap()).join("System32"));
    let mut child = command.spawn().unwrap();
    let mut input = child.stdin.take().unwrap();
    let output = child.stdout.take().unwrap();
    let (send, receive) = std::sync::mpsc::channel();
    let reader = std::thread::spawn(move || {
        use std::io::BufRead;
        let mut frame = String::new();
        let result = std::io::BufReader::new(output).read_line(&mut frame);
        let _ = send.send((result, frame));
    });
    input.write_all(b"{\"protocol_version\":1,\"id\":\"control\",\"method\":\"health\",\"params\":{}}\n").unwrap();
    input.flush().unwrap();
    let result = receive.recv_timeout(Duration::from_secs(30));
    let _ = child.kill();
    child.wait().unwrap();
    reader.join().unwrap();
    assert_eq!(temporary.parent(), Some(std::env::temp_dir().as_path()));
    no_links(&temporary).unwrap();
    fs::remove_dir_all(temporary).unwrap();
    let (_, frame) = result.expect("Synchronous control failed to receive health");
    assert!(decode(frame.as_bytes(), "control").is_ok());
}

fn runtime() -> tokio::runtime::Runtime {
    tokio::runtime::Builder::new_current_thread().enable_all().build().unwrap()
}

#[test]
fn framing_rejects_wrong_ids_duplicates_unknown_fields_and_both_variants() {
    let good = b"{\"protocol_version\":1,\"id\":\"a\",\"result\":{}}\n";
    assert!(decode(good, "a").is_ok());
    assert!(decode(good, "b").is_err());
    for frame in [
        b"{\"protocol_version\":1,\"id\":\"a\",\"id\":\"b\",\"result\":{}}\n".as_slice(),
        b"{\"protocol_version\":1,\"id\":\"a\",\"result\":[],\"unknown\":true}\n",
        b"{\"protocol_version\":1,\"id\":\"a\",\"result\":{},\"error\":{\"code\":\"BUSY\",\"message\":\"x\",\"retryable\":true}}\n",
        b"{\"protocol_version\":1,\"id\":\"a\",\"result\":{},\"error\":null}\n",
        b"{\"protocol_version\":2,\"id\":\"a\",\"result\":{}}\n",
        b"{\"protocol_version\":1,\"id\":\"a\",\"result\":{}}",
    ] { assert!(decode(frame, "a").is_err()); }
    assert!(decode(&vec![b'x'; FRAME_LIMIT + 1], "a").is_err());
}

#[test]
fn remote_errors_are_redacted_and_path_components_are_guarded() {
    let error = decode(b"{\"protocol_version\":1,\"id\":\"a\",\"error\":{\"code\":\"CONFLICT\",\"message\":\"private content\",\"retryable\":true}}\n", "a").unwrap_err();
    assert_eq!(error.code, "CONFLICT");
    assert!(!error.retryable);
    assert!(!error.message.contains("private"));
    for value in ["", "../x", "/x", "a/../x", "a//x", "C:/x", "a\\x", "a/NUL.txt", "a/x."] {
        assert!(relative_path(value).is_err(), "{value}");
    }
    assert!(relative_path("_internal/schemas/ipc.schema.json").is_ok());
}

#[test]
#[cfg(windows)]
fn actual_frozen_worker_persists_reopens_and_stops() {
    let _single_worker = PROCESS_TEST_LOCK.lock().unwrap_or_else(|error| error.into_inner());
    runtime().block_on(async {
        let bundle = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("resources/memory-worker");
        let temporary = std::env::temp_dir().join(format!("mp-rust-{}", uuid::Uuid::new_v4()));
        fs::create_dir(&temporary).unwrap();
        let vault = temporary.join("vault");
        let mut worker = Worker::start(&bundle, &vault, true).await.unwrap();
        assert!(worker.child.as_ref().unwrap().lock().unwrap().id().is_some());
        let receipt = worker.request("sessions.create", json!({"op_id":uuid::Uuid::new_v4().to_string(),"title":"Synthetic Rust test","body":"Summary","source_text":"Original\r\nதமிழ்"})).await.unwrap();
        assert!(worker.request("cloud.preview", json!({})).await.is_err());
        worker.stop().await.unwrap();
        assert!(worker.child.is_none() && worker.input.is_none() && worker.output.is_none());
        assert!(worker.request("health", json!({})).await.is_err());
        let mut reopened = Worker::start(&bundle, &vault, false).await.unwrap();
        let listed = reopened.request("sessions.list", json!({"limit":50,"offset":0})).await.unwrap();
        assert_eq!(listed["items"][0]["id"], receipt["id"]);
        let read = reopened.request("sessions.read", json!({"id":receipt["id"]})).await.unwrap();
        assert_eq!(read["source_text"], "Original\r\nதமிழ்");
        reopened.stop().await.unwrap();
        assert!(reopened.child.is_none() && reopened.input.is_none() && reopened.output.is_none());
        assert!(reopened.request("health", json!({})).await.is_err());
        // A separately held owned-child control can cancel startup before the
        // health await completes; it does not need the IO/request mutex.
        let mut control = None;
        let cancelled = Worker::start_supervised(&bundle, &vault, false, |child| {
            child.lock().unwrap().start_kill().unwrap();
            control = Some(child);
            Ok(())
        }).await;
        assert!(cancelled.is_err());
        assert!(control.unwrap().lock().unwrap().try_wait().unwrap().is_some());
        // Only this test's UUID-created temporary fixture is removed.
        assert_eq!(temporary.parent(), Some(std::env::temp_dir().as_path()));
        assert!(temporary.file_name().unwrap().to_str().unwrap().starts_with("mp-rust-"));
        no_links(&temporary).unwrap();
        fs::remove_dir_all(&temporary).unwrap();
    });
}

#[test]
fn partial_frames_oversize_eof_and_waiting_deadline() {
    runtime().block_on(async {
        let (client, mut server) = tokio::io::duplex(2048);
        let sender = tokio::spawn(async move {
            server.write_all(b"{\"protocol_version\":1,").await.unwrap();
            tokio::task::yield_now().await;
            server.write_all(b"\"id\":\"a\",\"result\":{}}\n").await.unwrap();
        });
        let frame = read_frame(&mut BufReader::new(client)).await.unwrap();
        assert!(decode(&frame, "a").is_ok());
        sender.await.unwrap();

        let (client, mut server) = tokio::io::duplex(2048);
        let sender = tokio::spawn(async move { server.write_all(&vec![b'x'; FRAME_LIMIT + 1]).await.unwrap(); });
        assert!(read_frame(&mut BufReader::new(client)).await.is_err());
        sender.await.unwrap();

        let (client, mut server) = tokio::io::duplex(2048);
        server.write_all(b"truncated").await.unwrap();
        drop(server);
        assert!(read_frame(&mut BufReader::new(client)).await.is_err());

        let (client, _open_server) = tokio::io::duplex(2048);
        assert!(timeout(Duration::from_millis(10), read_frame(&mut BufReader::new(client))).await.is_err());
    });
}
