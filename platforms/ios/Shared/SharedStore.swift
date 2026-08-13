import Foundation

/// Read/write ClarityIME state via App Group UserDefaults.
final class SharedStore {
    static let shared = SharedStore()

    private let defaults: UserDefaults

    init(suiteName: String = AppGroupConstants.suiteName) {
        defaults = UserDefaults(suiteName: suiteName) ?? .standard
    }

    // MARK: - Settings

    var audienceMode: String {
        get { defaults.string(forKey: AppGroupConstants.audienceMode) ?? "default" }
        set { defaults.set(newValue, forKey: AppGroupConstants.audienceMode) }
    }

    var defaultContact: String? {
        get { defaults.string(forKey: AppGroupConstants.defaultContact)?.nilIfEmpty }
        set { defaults.set(newValue ?? "", forKey: AppGroupConstants.defaultContact) }
    }

    var asrLanguage: String {
        get { defaults.string(forKey: AppGroupConstants.asrLanguage) ?? AppGroupConstants.defaultASRLanguage }
        set { defaults.set(newValue, forKey: AppGroupConstants.asrLanguage) }
    }

    var autoApplyTop: Bool {
        get { defaults.bool(forKey: AppGroupConstants.autoApplyTop) }
        set { defaults.set(newValue, forKey: AppGroupConstants.autoApplyTop) }
    }

    var onboardingCompleted: Bool {
        get { defaults.bool(forKey: AppGroupConstants.onboardingCompleted) }
        set { defaults.set(newValue, forKey: AppGroupConstants.onboardingCompleted) }
    }

    var localApiToken: String {
        get { defaults.string(forKey: AppGroupConstants.localApiToken) ?? "" }
        set { defaults.set(newValue, forKey: AppGroupConstants.localApiToken) }
    }

    func markOnboardingCompleted() {
        onboardingCompleted = true
        defaults.synchronize()
    }

    func resetOnboarding() {
        onboardingCompleted = false
        defaults.synchronize()
    }

    var contactHints: ContactHints {
        get {
            guard
                let data = defaults.data(forKey: AppGroupConstants.contactHintsJSON),
                let decoded = try? JSONDecoder().decode(ContactHints.self, from: data)
            else { return .empty }
            return decoded
        }
        set {
            if let data = try? JSONEncoder().encode(newValue) {
                defaults.set(data, forKey: AppGroupConstants.contactHintsJSON)
            }
        }
    }

    func saveSettings(
        mode: String,
        contact: String?,
        language: String,
        hints: ContactHints,
        autoApplyTop: Bool? = nil,
        localApiToken: String? = nil
    ) {
        audienceMode = mode
        defaultContact = contact
        asrLanguage = language
        contactHints = hints
        if let autoApplyTop { self.autoApplyTop = autoApplyTop }
        if let localApiToken { self.localApiToken = localApiToken }
        defaults.synchronize()
    }

    // MARK: - Voice pipeline

    var voiceSessionID: Int {
        get { defaults.integer(forKey: AppGroupConstants.voiceSessionID) }
        set { defaults.set(newValue, forKey: AppGroupConstants.voiceSessionID) }
    }

    var voiceRawText: String {
        get { defaults.string(forKey: AppGroupConstants.voiceRawText) ?? "" }
        set { defaults.set(newValue, forKey: AppGroupConstants.voiceRawText) }
    }

    var voicePendingCommit: Bool {
        get { defaults.bool(forKey: AppGroupConstants.voicePendingCommit) }
        set { defaults.set(newValue, forKey: AppGroupConstants.voicePendingCommit) }
    }

    var voiceUpdatedAt: Date? {
        get { defaults.object(forKey: AppGroupConstants.voiceUpdatedAt) as? Date }
        set { defaults.set(newValue, forKey: AppGroupConstants.voiceUpdatedAt) }
    }

    var voiceStatusMessage: String {
        get { defaults.string(forKey: AppGroupConstants.voiceStatusMessage) ?? "" }
        set { defaults.set(newValue, forKey: AppGroupConstants.voiceStatusMessage) }
    }

    var voiceNbest: [String] {
        get {
            guard
                let json = defaults.string(forKey: AppGroupConstants.voiceNbestJSON),
                let data = json.data(using: .utf8),
                let decoded = try? JSONDecoder().decode([String].self, from: data)
            else { return [] }
            return decoded
        }
        set {
            if let data = try? JSONEncoder().encode(newValue),
               let json = String(data: data, encoding: .utf8) {
                defaults.set(json, forKey: AppGroupConstants.voiceNbestJSON)
            } else {
                defaults.removeObject(forKey: AppGroupConstants.voiceNbestJSON)
            }
        }
    }

    var voiceCandidates: [ClarifyCandidate] {
        get {
            guard
                let json = defaults.string(forKey: AppGroupConstants.voiceCandidatesJSON),
                let data = json.data(using: .utf8),
                let decoded = try? JSONDecoder().decode([ClarifyCandidate].self, from: data)
            else { return [] }
            return decoded
        }
        set {
            if let data = try? JSONEncoder().encode(newValue),
               let json = String(data: data, encoding: .utf8) {
                defaults.set(json, forKey: AppGroupConstants.voiceCandidatesJSON)
            } else {
                defaults.removeObject(forKey: AppGroupConstants.voiceCandidatesJSON)
            }
        }
    }

    /// Host: publish a completed voice session for the keyboard extension.
    func publishVoiceResult(
        raw: String,
        candidates: [ClarifyCandidate],
        nbest: [String] = [],
        status: String = "ready"
    ) {
        voiceSessionID += 1
        voiceRawText = raw
        voiceNbest = nbest
        voiceCandidates = candidates
        voicePendingCommit = true
        voiceUpdatedAt = Date()
        voiceStatusMessage = status
        defaults.synchronize()
    }

    /// Keyboard: mark candidates consumed after user picks one.
    func clearVoicePending() {
        voicePendingCommit = false
        voiceStatusMessage = "committed"
        defaults.synchronize()
    }

    /// Host: update live status while listening.
    func setVoiceStatus(_ message: String) {
        voiceStatusMessage = message
        defaults.synchronize()
    }

    // MARK: - Offline feedback queue (keyboard enqueue, host flush)

    var pendingFeedbacks: [PendingFeedback] {
        get {
            guard
                let data = defaults.data(forKey: AppGroupConstants.pendingFeedbackJSON),
                let decoded = try? JSONDecoder().decode([PendingFeedback].self, from: data)
            else { return [] }
            return decoded
        }
        set {
            if newValue.isEmpty {
                defaults.removeObject(forKey: AppGroupConstants.pendingFeedbackJSON)
            } else if let data = try? JSONEncoder().encode(newValue) {
                defaults.set(data, forKey: AppGroupConstants.pendingFeedbackJSON)
            }
            defaults.synchronize()
        }
    }

    func enqueuePendingFeedback(_ item: PendingFeedback) {
        var items = pendingFeedbacks
        items.append(item)
        pendingFeedbacks = items
    }

    func replacePendingFeedbacks(_ items: [PendingFeedback]) {
        pendingFeedbacks = items
    }
}

private extension String {
    var nilIfEmpty: String? {
        trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : self
    }
}
