import Foundation

/// Offline clarification rules used when the core API is unreachable.
public enum ClarityOfflineClarifier {
    private static let fillers = ["嗯", "啊", "那个", "就是"]
    private static let sentenceEnders = CharacterSet(charactersIn: "。！？")

    public static func clarify(_ text: String, mode: String) -> String {
        var t = text.trimmingCharacters(in: .whitespaces)
        for filler in fillers where t.hasPrefix(filler) {
            t = String(t.dropFirst(filler.count))
        }
        t = t.trimmingCharacters(in: .whitespaces)

        if mode == "ai" {
            return "Intent: \(t.trimmingCharacters(in: sentenceEnders))"
        }
        if !t.isEmpty, let last = t.last, !sentenceEnders.contains(String(last)) {
            t += t.contains("吗") ? "？" : "。"
        }
        return t
    }
}
