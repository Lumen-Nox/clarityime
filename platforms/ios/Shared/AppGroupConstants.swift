import Foundation

/// App Group identifiers and UserDefaults keys shared between ClarityHost and ClarityKeyboard.
enum AppGroupConstants {
    static let suiteName = "group.com.clarityime"

    // Settings (written by host, read by keyboard)
    static let audienceMode = "audience_mode"
    static let defaultContact = "default_contact"
    static let asrLanguage = "asr_language"
    static let contactHintsJSON = "contact_hints_json"
    static let autoApplyTop = "auto_apply_top"
    static let onboardingCompleted = "onboarding_completed"
    static let localApiToken = "local_api_token"

    // Voice pipeline (host writes, keyboard reads)
    static let voiceSessionID = "voice_session_id"
    static let voiceRawText = "voice_raw_text"
    static let voiceCandidatesJSON = "voice_candidates_json"
    static let voicePendingCommit = "voice_pending_commit"
    static let voiceUpdatedAt = "voice_updated_at"
    static let voiceStatusMessage = "voice_status_message"
    static let voiceNbestJSON = "voice_nbest_json"
    static let pendingFeedbackJSON = "pending_feedback_json"

    static let defaultASRLanguage = "zh-CN"
}

/// Lightweight contact hints for offline contact-mode clarify (placeholder until core sync).
struct ContactHints: Codable, Equatable {
    var name: String
    var relationship: String
    var style: String
    var age: String
    var words: String

    static let empty = ContactHints(
        name: "",
        relationship: "",
        style: "",
        age: "",
        words: ""
    )

    func toHintDictionary() -> [String: String] {
        [
            "relationship": relationship,
            "style": style,
            "age": age,
            "words": words,
        ]
    }
}

struct ClarifyCandidate: Codable, Equatable {
    let text: String
    let label: String
}

struct ContactRow: Codable, Equatable {
    let id: String
    let name: String
    let relationship: String
    let styleNotes: String
    let comprehensionNotes: String
    var ceromeSummary: String = ""

    enum CodingKeys: String, CodingKey {
        case id, name, relationship
        case styleNotes = "style_notes"
        case comprehensionNotes = "comprehension_notes"
        case ceromeSummary = "cerome_summary"
    }
}
