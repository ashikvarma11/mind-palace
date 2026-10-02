use super::*;

fn runtime() -> tokio::runtime::Runtime {
    tokio::runtime::Builder::new_current_thread().enable_all().build().unwrap()
}
fn id() -> String { uuid::Uuid::new_v4().to_string() }

#[test]
fn cancellation_is_targeted_and_single_flight_survives_until_cleanup() {
    let requests = Requests::default();
    assert!(requests.begin("../key").is_err());
    let first = id();
    let held = requests.begin(&first).unwrap();
    assert!(requests.begin(&id()).is_err());
    assert!(!requests.cancel(&id()).unwrap());
    assert!(requests.cancel(&first).unwrap());
    assert!(requests.cancel(&first).unwrap());
    assert!(requests.begin(&id()).is_err());
    drop(held);
    assert!(requests.begin(&first).is_err());
    let second = id();
    let _next = requests.begin(&second).unwrap();
    assert!(!requests.cancel(&first).unwrap());
}

#[test]
fn identifiers_are_bounded_without_reusing_old_cancellation_targets() {
    let requests = Requests::default();
    for _ in 0..4096 { drop(requests.begin(&id()).unwrap()); }
    assert!(requests.begin(&id()).is_err());
}

#[test]
fn precancel_wins_without_polling_work_and_completion_is_not_retried() {
    runtime().block_on(async {
        let requests = Requests::default();
        let first = id();
        let mut held = requests.begin(&first).unwrap();
        requests.cancel(&first).unwrap();
        let error = held.run(async { panic!("Cancelled work must never be polled") }, Duration::from_secs(1)).await.unwrap_err();
        assert_eq!(error.code, "AI_CANCELLED");
        drop(held);
        let mut held = requests.begin(&id()).unwrap();
        assert_eq!(held.run(async { 42 }, Duration::from_secs(1)).await.unwrap(), 42);
    });
}

#[test]
fn pending_work_is_cancelled_or_times_out_and_its_future_is_dropped() {
    struct Dropped<'a>(&'a std::sync::atomic::AtomicBool);
    impl Drop for Dropped<'_> {
        fn drop(&mut self) { self.0.store(true, std::sync::atomic::Ordering::SeqCst); }
    }
    runtime().block_on(async {
        let requests = std::sync::Arc::new(Requests::default());
        let first = id();
        let mut held = requests.begin(&first).unwrap();
        let controller = requests.clone();
        let task = tokio::spawn(async move {
            tokio::time::sleep(Duration::from_millis(10)).await;
            controller.cancel(&first).unwrap();
        });
        let dropped = std::sync::atomic::AtomicBool::new(false);
        let owned = Dropped(&dropped);
        let error = held.run(async move {
            let _owned = owned;
            std::future::pending::<()>().await;
        }, Duration::from_secs(1)).await.unwrap_err();
        assert_eq!(error.code, "AI_CANCELLED");
        assert!(dropped.load(std::sync::atomic::Ordering::SeqCst));
        task.await.unwrap();
        drop(held);
        let mut next = requests.begin(&id()).unwrap();
        let error = next.run(std::future::pending::<()>(), Duration::from_millis(10)).await.unwrap_err();
        assert_eq!(error.code, "AI_TIMEOUT");
    });
}
