import Foundation

/// Loopback API token for mutating ClarityIME core endpoints (v0.4+).
enum LocalApiAuth {
    private static let envToken = "CLARITYIME_API_TOKEN"
    private static let envRoot = "CLARITYIME_ROOT"
    private static let defaultsKey = "local_api_token"
    private static let appGroupKey = AppGroupConstants.localApiToken

    static func token() -> String? {
        if let env = ProcessInfo.processInfo.environment[envToken]?.trimmingCharacters(in: .whitespacesAndNewlines),
           !env.isEmpty {
            return env
        }
        if let suite = UserDefaults(suiteName: AppGroupConstants.suiteName),
           let stored = suite.string(forKey: appGroupKey)?
            .trimmingCharacters(in: .whitespacesAndNewlines),
           !stored.isEmpty {
            return stored
        }
        if let stored = UserDefaults.standard.string(forKey: defaultsKey)?
            .trimmingCharacters(in: .whitespacesAndNewlines),
           !stored.isEmpty {
            return stored
        }
        for path in tokenFileCandidates() {
            if let text = try? String(contentsOfFile: path, encoding: .utf8)
                .trimmingCharacters(in: .whitespacesAndNewlines),
               !text.isEmpty {
                return text
            }
        }
        return nil
    }

    private static func tokenFileCandidates() -> [String] {
        var paths: [String] = []
        if let root = ProcessInfo.processInfo.environment[envRoot]?
            .trimmingCharacters(in: .whitespacesAndNewlines),
           !root.isEmpty {
            paths.append((root as NSString).appendingPathComponent("data/.local_api_token"))
        }
        let home = NSHomeDirectory()
        paths.append((home as NSString).appendingPathComponent("clarityime/data/.local_api_token"))
        return paths
    }
}
