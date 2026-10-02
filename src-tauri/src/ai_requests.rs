//! Cancellation control only. No keys, HTTP, retries, or detached tasks.
use crate::worker::Error;
use std::{collections::BTreeSet, future::{poll_fn, Future}, sync::Mutex, task::Poll, time::Duration};
use tokio::sync::watch;

#[derive(Default)]
pub(crate) struct Requests { state: Mutex<State> }
#[derive(Default)]
struct State { active: Option<Active>, seen: BTreeSet<String> }
struct Active { id: String, cancel: watch::Sender<bool> }
pub(crate) struct Request<'a> { owner: &'a Requests, id: String, cancel: watch::Receiver<bool> }

fn failure(code: &'static str, message: &'static str) -> Error {
    Error { code, message, retryable: false }
}

impl Requests {
    pub(crate) fn begin(&self, id: &str) -> Result<Request<'_>, Error> {
        if !uuid::Uuid::parse_str(id).is_ok_and(|parsed| parsed.to_string() == id) {
            return Err(failure("VALIDATION_ERROR", "The AI request identifier is invalid."));
        }
        let mut state = self.state.lock().map_err(|_| failure("INTERNAL_ERROR", "AI request control is unavailable."))?;
        if state.active.is_some() { return Err(failure("BUSY", "Another AI request is still running.")); }
        if state.seen.contains(id) { return Err(failure("CONFLICT", "Use a fresh AI request identifier.")); }
        if state.seen.len() >= 4096 { return Err(failure("LIMIT_EXCEEDED", "Restart the app before making more AI requests.")); }
        let (send, receive) = watch::channel(false);
        state.seen.insert(id.to_owned());
        state.active = Some(Active { id: id.to_owned(), cancel: send });
        Ok(Request { owner: self, id: id.to_owned(), cancel: receive })
    }

    pub(crate) fn cancel(&self, id: &str) -> Result<bool, Error> {
        let state = self.state.lock().map_err(|_| failure("INTERNAL_ERROR", "AI request control is unavailable."))?;
        let Some(active) = state.active.as_ref().filter(|active| active.id == id) else { return Ok(false); };
        // Retain BUSY until the owning future has completed its cleanup.
        active.cancel.send_replace(true);
        Ok(true)
    }
}

impl Request<'_> {
    pub(crate) async fn run<T>(&mut self, future: impl Future<Output = T>, deadline: Duration) -> Result<T, Error> {
        let mut work = std::pin::pin!(tokio::time::timeout(deadline, future));
        let cancel = &mut self.cancel;
        let mut cancelled = std::pin::pin!(async {
            loop {
                if *cancel.borrow_and_update() { break; }
                if cancel.changed().await.is_err() { break; }
            }
        });
        poll_fn(|cx| {
            // Cancellation wins if both work and cancellation are ready.
            if cancelled.as_mut().poll(cx).is_ready() {
                return Poll::Ready(Err(failure("AI_CANCELLED", "AI request cancelled. Reopen the vault before another preview.")));
            }
            match work.as_mut().poll(cx) {
                Poll::Ready(Ok(result)) => Poll::Ready(Ok(result)),
                Poll::Ready(Err(_)) => Poll::Ready(Err(failure("AI_TIMEOUT", "AI request timed out. Reopen the vault before another preview."))),
                Poll::Pending => Poll::Pending,
            }
        }).await
    }
}

impl Drop for Request<'_> {
    fn drop(&mut self) {
        let mut state = self.owner.state.lock().unwrap_or_else(|error| error.into_inner());
        if state.active.as_ref().is_some_and(|active| active.id == self.id) { state.active = None; }
    }
}

#[cfg(test)]
#[path = "ai_requests_tests.rs"]
mod tests;
