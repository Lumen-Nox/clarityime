import Foundation

/// Offline-safe feedback: POST when core is up, else queue in App Group for Host flush.
enum FeedbackSync {
    enum Result {
        case sent(bundleURL: String)
        case queued
    }

    static func submit(
        raw: String,
        preferred: String,
        nbest: [String],
        candidates: [ClarifyCandidate],
        mode: String
    ) -> Result {
        if let url = ClarifyClient.feedback(
            raw: raw,
            preferred: preferred,
            nbest: nbest,
            candidates: candidates,
            mode: mode
        ) {
            return .sent(bundleURL: url)
        }
        SharedStore.shared.enqueuePendingFeedback(
            PendingFeedback(
                raw: raw,
                preferred: preferred,
                nbest: nbest,
                candidates: candidates,
                mode: mode,
                createdAt: Date()
            )
        )
        return .queued
    }

    /// Host calls on launch / when core URL changes. Returns number successfully flushed.
    @discardableResult
    static func flushPending() -> Int {
        let store = SharedStore.shared
        var pending = store.pendingFeedbacks
        guard !pending.isEmpty else { return 0 }

        var sent = 0
        var remaining: [PendingFeedback] = []
        for item in pending {
            if let _ = ClarifyClient.feedback(
                raw: item.raw,
                preferred: item.preferred,
                nbest: item.nbest,
                candidates: item.candidates,
                mode: item.mode,
                timeout: 2.0
            ) {
                sent += 1
            } else {
                remaining.append(item)
            }
        }
        store.replacePendingFeedbacks(remaining)
        return sent
    }
}

struct PendingFeedback: Codable, Equatable {
    let raw: String
    let preferred: String
    let nbest: [String]
    let candidates: [ClarifyCandidate]
    let mode: String
    let createdAt: Date
}
