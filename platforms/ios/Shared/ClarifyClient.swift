import Foundation

/// Optional HTTP client for `clarityime serve` on LAN (usually unavailable on iOS).
enum ClarifyClient {
    private static let baseURL = URL(string: "http://127.0.0.1:17800")!

    private static func applyAuth(_ request: inout URLRequest) {
        if let token = LocalApiAuth.token() {
            request.setValue(token, forHTTPHeaderField: "X-ClarityIME-Token")
        }
    }

    static func health(timeout: TimeInterval = 0.4) -> Bool {
        var request = URLRequest(url: baseURL.appendingPathComponent("/v1/health"))
        request.timeoutInterval = timeout
        guard let (data, _) = try? URLSession.shared.syncData(for: request),
              let body = String(data: data, encoding: .utf8) else { return false }
        return body.contains("ok")
    }

    static func listContacts(timeout: TimeInterval = 0.8) -> [ContactRow] {
        guard health(timeout: timeout) else { return [] }
        var request = URLRequest(url: baseURL.appendingPathComponent("/v1/contacts"))
        request.timeoutInterval = timeout
        guard
            let (data, _) = try? URLSession.shared.syncData(for: request),
            let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
            let arr = json["contacts"] as? [[String: Any]]
        else { return [] }
        return arr.compactMap { item in
            guard let name = item["name"] as? String else { return nil }
            let idVal = item["id"]
            let id: String
            if let n = idVal as? Int { id = String(n) }
            else if let s = idVal as? String { id = s }
            else { id = "" }
            return ContactRow(
                id: id,
                name: name,
                relationship: item["relationship"] as? String ?? "",
                styleNotes: item["style_notes"] as? String ?? "",
                comprehensionNotes: item["comprehension_notes"] as? String ?? "",
                ceromeSummary: summarizeCerome(item["cerome"] as? [String: Any])
            )
        }
    }

    static func exportContactBundle(name: String, timeout: TimeInterval = 0.8) -> String? {
        guard health(timeout: timeout) else { return nil }
        guard let encoded = name.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) else { return nil }
        var request = URLRequest(url: baseURL.appendingPathComponent("/v1/contacts/export?name=\(encoded)"))
        request.timeoutInterval = timeout
        guard let (data, _) = try? URLSession.shared.syncData(for: request) else { return nil }
        return String(data: data, encoding: .utf8)
    }

    static func importContactBundle(json: String, timeout: TimeInterval = 0.8) -> Bool {
        guard health(timeout: timeout) else { return false }
        var request = URLRequest(url: baseURL.appendingPathComponent("/v1/contacts/import"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        applyAuth(&request)
        request.httpBody = json.data(using: .utf8)
        request.timeoutInterval = timeout
        guard let (_, resp) = try? URLSession.shared.syncData(for: request),
              let http = resp as? HTTPURLResponse else { return false }
        return (200...299).contains(http.statusCode)
    }

    static func candidates(
        text: String,
        mode: String,
        contact: String?,
        nbest: [String]? = nil,
        timeout: TimeInterval = 0.8
    ) -> [ClarifyCandidate]? {
        guard health(timeout: timeout) else { return nil }
        var request = URLRequest(url: baseURL.appendingPathComponent("/v1/candidates"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = timeout
        var body: [String: Any] = ["text": text, "mode": mode]
        if let contact { body["contact"] = contact }
        if let nbest, !nbest.isEmpty { body["nbest"] = nbest }
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        guard
            let (data, _) = try? URLSession.shared.syncData(for: request),
            let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
            let arr = json["candidates"] as? [[String: Any]]
        else { return nil }
        return arr.compactMap { item in
            guard let t = item["text"] as? String else { return nil }
            return ClarifyCandidate(text: t, label: item["label"] as? String ?? "option")
        }
    }

    static func feedback(
        raw: String,
        preferred: String,
        nbest: [String]? = nil,
        candidates: [ClarifyCandidate]? = nil,
        mode: String? = nil,
        timeout: TimeInterval = 0.8
    ) -> String? {
        var request = URLRequest(url: baseURL.appendingPathComponent("/v1/feedback"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        applyAuth(&request)
        request.timeoutInterval = timeout
        var body: [String: Any] = ["raw": raw, "preferred": preferred]
        if let nbest, !nbest.isEmpty { body["nbest"] = nbest }
        if let candidates, !candidates.isEmpty {
            body["candidates"] = candidates.map { ["text": $0.text, "label": $0.label] }
        }
        if let mode { body["mode"] = mode }
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        guard
            let (data, _) = try? URLSession.shared.syncData(for: request),
            let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
            let url = json["bundle_url"] as? String,
            !url.isEmpty
        else { return nil }
        return url
    }

    static func saveContact(
        name: String,
        relationship: String,
        styleNotes: String,
        comprehensionNotes: String,
        ceromeL2: [String: Double]? = nil,
        moodLabel: String = "steady",
        timeout: TimeInterval = 0.8
    ) -> Bool {
        guard health(timeout: timeout) else { return false }
        var request = URLRequest(url: baseURL.appendingPathComponent("/v1/contacts"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        applyAuth(&request)
        request.timeoutInterval = timeout
        var cerome: [String: Any] = [
            "L5": ["label": moodLabel],
            "L4": ["formality": ["老师", "教授", "上级", "老板"].contains(relationship) ? 0.7 : 0.45],
        ]
        if let ceromeL2 {
            cerome["L2"] = ceromeL2
        }
        let body: [String: Any] = [
            "name": name,
            "relationship": relationship,
            "style_notes": styleNotes,
            "comprehension_notes": comprehensionNotes,
            "cerome": cerome,
        ]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        guard let (_, resp) = try? URLSession.shared.syncData(for: request),
              let http = resp as? HTTPURLResponse else { return false }
        return (200...299).contains(http.statusCode)
    }

    private static func summarizeCerome(_ cerome: [String: Any]?) -> String {
        guard let cerome else { return "" }
        let l5 = (cerome["L5"] as? [String: Any])?["label"] as? String
        guard let l2 = cerome["L2"] as? [String: Any] else {
            return l5 ?? ""
        }
        let ranked = ["clarity", "warmth", "efficiency", "precision", "humor"]
            .compactMap { key -> (String, Double)? in
                guard let v = l2[key] as? Double else { return nil }
                return (key, v)
            }
            .sorted { $0.1 > $1.1 }
            .prefix(2)
            .map(\.0)
        let parts = [l5, ranked.joined(separator: ",")].compactMap { $0 }.filter { !$0.isEmpty }
        return parts.joined(separator: " · ")
    }
}

extension URLSession {
    func syncData(for request: URLRequest) throws -> (Data, URLResponse) {
        var result: (Data, URLResponse)?
        var thrown: Error?
        let sem = DispatchSemaphore(value: 0)
        let task = dataTask(with: request) { data, response, error in
            if let error { thrown = error }
            else if let data, let response { result = (data, response) }
            sem.signal()
        }
        task.resume()
        sem.wait()
        if let thrown { throw thrown }
        guard let result else { throw URLError(.badServerResponse) }
        return result
    }
}
