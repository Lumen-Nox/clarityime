import Foundation

/// Offline clarification — mirrors Python `local_rules.py` (deterministic, no LLM).
/// Preserve detail & tone; never summarize.
enum ClarifyRules {
    private static let fillers = ["嗯", "啊", "呃", "那个", "就是", "然后", "你知道", "怎么说呢", "对对对"]
    private static let questionMarkers = ["吗", "么", "是不是", "能不能", "什么", "怎么", "哪", "谁"]
    private static let clauseBreakers = ["因为", "但是", "所以", "而且", "不过", "然而"]
    private static let formalRelationships = ["老师", "教授", "上级", "老板"]
    private static let terminalPunctuation = CharacterSet(charactersIn: "。！？.!?")

    static func normalizeMode(_ mode: String) -> String {
        switch mode.trimmingCharacters(in: .whitespacesAndNewlines).lowercased() {
        case "ai": return "structured"
        default: return mode.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        }
    }

    static func candidates(
        text: String,
        mode: String,
        contactHints: ContactHints = .empty
    ) -> [ClarifyCandidate] {
        switch normalizeMode(mode) {
        case "structured":
            return candidatesForStructured(text)
        case "contact":
            return candidatesForContact(text, hints: contactHints)
        default:
            return candidatesDefault(text)
        }
    }

    static func clarifyDefault(_ text: String) -> String {
        var out = stripFillers(text)
        out = insertClauseBreaks(out)
        out = punctuate(out)
        return out.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    static func clarifyForStructured(_ text: String) -> String {
        let out = clarifyDefault(text)
        let sents = out
            .components(separatedBy: CharacterSet(charactersIn: "。！？"))
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
        guard sents.count >= 2 else { return out }
        return sents.map { punctuate($0) }.joined(separator: "\n\n")
    }

    static func clarifyForContact(_ text: String, hints: ContactHints) -> String {
        var out = clarifyDefault(text)
        let hintMap = hints.toHintDictionary()
        let rel = hintMap["relationship"] ?? ""
        let style = hintMap["style"] ?? ""
        let words = hintMap["words"] ?? ""
        let warm = style.contains("温和")

        if !words.isEmpty {
            for pair in words.split(separator: ",") {
                let parts = pair.split(separator: "->", maxSplits: 1).map {
                    String($0).trimmingCharacters(in: .whitespaces)
                }
                if parts.count == 2 {
                    out = out.replacingOccurrences(of: parts[0], with: parts[1])
                }
            }
        }
        if formalRelationships.contains(rel) || style.contains("正式") {
            out = out.replacingOccurrences(of: "你", with: "您")
            if ["老师", "教授"].contains(rel), !out.hasPrefix("老师"), questionMarkers.contains(where: { out.contains($0) }) {
                out = "老师，" + out
            }
        }
        if warm, (out.contains("去不了") || out.contains("晚一天")), !out.contains("不好意思") {
            out = "不好意思，" + out
        }
        return punctuate(out)
    }

    private static func candidatesDefault(_ text: String) -> [ClarifyCandidate] {
        let primary = clarifyDefault(text)
        var options: [ClarifyCandidate] = [ClarifyCandidate(text: primary, label: "standard")]
        if !primary.contains("我"), text.contains("想") {
            let explicit = "我想" + primary.trimmingCharacters(in: CharacterSet(charactersIn: "我想"))
            if explicit != primary {
                options.append(ClarifyCandidate(text: explicit, label: "explicit_subject"))
            }
        }
        return dedupe(options, limit: 3)
    }

    private static func candidatesForStructured(_ text: String) -> [ClarifyCandidate] {
        let primary = clarifyForStructured(text)
        var options: [ClarifyCandidate] = [ClarifyCandidate(text: primary, label: "structured")]
        let flat = primary.replacingOccurrences(of: "\n", with: "")
        if flat != primary {
            options.append(ClarifyCandidate(text: flat, label: "continuous"))
        }
        return dedupe(options, limit: 3)
    }

    private static func candidatesForContact(_ text: String, hints: ContactHints) -> [ClarifyCandidate] {
        let primary = clarifyForContact(text, hints: hints)
        return dedupe([ClarifyCandidate(text: primary, label: "for_contact")], limit: 3)
    }

    private static func stripFillers(_ text: String) -> String {
        var out = text.trimmingCharacters(in: .whitespacesAndNewlines)
        let leadingPattern = "^(嗯+|啊+|呃+|那个+|就是+|然后+)\\s*"
        if let regex = try? NSRegularExpression(pattern: leadingPattern) {
            let range = NSRange(out.startIndex..., in: out)
            out = regex.stringByReplacingMatches(in: out, range: range, withTemplate: "")
        }
        for filler in fillers {
            if let regex = try? NSRegularExpression(pattern: NSRegularExpression.escapedPattern(for: filler) + "+") {
                let range = NSRange(out.startIndex..., in: out)
                out = regex.stringByReplacingMatches(in: out, options: [], range: range, withTemplate: "")
            }
        }
        out = out.replacingOccurrences(of: "^那个啥[，,、\\s]+", with: "", options: .regularExpression)
        out = out.replacingOccurrences(of: "^我跟你说啊?[，,、\\s]+", with: "", options: .regularExpression)
        return dedupeSpaces(out)
    }

    private static func insertClauseBreaks(_ text: String) -> String {
        var out = text
        for word in clauseBreakers {
            if let regex = try? NSRegularExpression(pattern: "(?<=[^，,；;])\(NSRegularExpression.escapedPattern(for: word))") {
                let range = NSRange(out.startIndex..., in: out)
                out = regex.stringByReplacingMatches(in: out, range: range, withTemplate: "，\(word)")
            }
        }
        out = out.replacingOccurrences(of: "，然后", with: "，")
        return out
    }

    private static func punctuate(_ text: String) -> String {
        var t = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !t.isEmpty else { return t }
        if let last = t.unicodeScalars.last, terminalPunctuation.contains(last) { return t }
        t += questionMarkers.contains(where: { t.contains($0) }) ? "？" : "。"
        return t
    }

    private static func dedupeSpaces(_ text: String) -> String {
        text
            .components(separatedBy: .whitespaces)
            .filter { !$0.isEmpty }
            .joined(separator: " ")
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private static func dedupe(_ options: [ClarifyCandidate], limit: Int) -> [ClarifyCandidate] {
        var seen = Set<String>()
        var out: [ClarifyCandidate] = []
        for opt in options {
            let key = opt.text.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !key.isEmpty, !seen.contains(key) else { continue }
            seen.insert(key)
            out.append(ClarifyCandidate(text: key, label: opt.label))
            if out.count >= limit { break }
        }
        return out
    }
}
