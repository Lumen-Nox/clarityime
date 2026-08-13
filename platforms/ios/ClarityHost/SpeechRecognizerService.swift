import AVFoundation
import Speech
import SwiftUI

/// Host-app speech recognition → clarify → App Group for keyboard extension.
@MainActor
final class SpeechRecognizerService: ObservableObject {
    @Published var isListening = false
    @Published var isAuthorized = false
    @Published var partialText = ""
    @Published var statusMessage = ""
    @Published var lastCandidates: [ClarifyCandidate] = []
    @Published var lastNbest: [String] = []

    private let store = SharedStore.shared
    private let audioEngine = AVAudioEngine()
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var task: SFSpeechRecognitionTask?
    private let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "zh-CN"))

    func requestAuthorization() {
        SFSpeechRecognizer.requestAuthorization { [weak self] status in
            Task { @MainActor in
                self?.isAuthorized = status == .authorized
                if status != .authorized {
                    self?.statusMessage = "Speech permission denied — enable in Settings"
                }
            }
        }
        AVAudioApplication.requestRecordPermission { [weak self] granted in
            Task { @MainActor in
                if !granted {
                    self?.statusMessage = "Microphone permission denied"
                }
            }
        }
    }

    func toggleListening() {
        isListening ? stopListening() : startListening()
    }

    func startListening() {
        guard isAuthorized else {
            requestAuthorization()
            return
        }
        stopListening()

        partialText = ""
        lastCandidates = []
        lastNbest = []
        statusMessage = "Listening…"
        store.setVoiceStatus("listening")

        request = SFSpeechAudioBufferRecognitionRequest()
        request?.shouldReportPartialResults = true

        let inputNode = audioEngine.inputNode
        guard let request else { return }

        task = recognizer?.recognitionTask(with: request) { [weak self] result, error in
            Task { @MainActor in
                guard let self else { return }
                if let result {
                    self.partialText = result.bestTranscription.formattedString
                    if result.isFinal {
                        let nbest = result.transcriptions
                            .map { $0.formattedString.trimmingCharacters(in: .whitespacesAndNewlines) }
                            .filter { !$0.isEmpty }
                        self.lastNbest = Array(Set(nbest)).prefix(5).map { $0 }
                        self.finishWithRaw(self.partialText, nbest: self.lastNbest)
                    }
                }
                if error != nil {
                    self.stopListening()
                }
            }
        }

        let format = inputNode.outputFormat(forBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: format) { buffer, _ in
            request.append(buffer)
        }

        do {
            try audioEngine.start()
            isListening = true
        } catch {
            statusMessage = "Audio engine failed: \(error.localizedDescription)"
            stopListening()
        }
    }

    func stopListening() {
        if isListening {
            audioEngine.stop()
            audioEngine.inputNode.removeTap(onBus: 0)
        }
        request?.endAudio()
        task?.cancel()
        request = nil
        task = nil
        isListening = false
        if !partialText.isEmpty && lastCandidates.isEmpty {
            finishWithRaw(partialText, nbest: lastNbest)
        }
    }

    private func finishWithRaw(_ raw: String, nbest: [String] = []) {
        let trimmed = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            statusMessage = "No speech detected"
            store.setVoiceStatus("empty")
            return
        }

        let mode = store.audienceMode
        let contact = store.defaultContact
        let hypotheses = nbest.isEmpty ? [trimmed] : nbest
        lastNbest = hypotheses

        let remote = ClarifyClient.candidates(
            text: trimmed,
            mode: mode,
            contact: contact,
            nbest: hypotheses
        )
        let candidates = remote ?? ClarifyRules.candidates(
            text: trimmed,
            mode: mode,
            contactHints: store.contactHints
        )
        lastCandidates = candidates
        store.publishVoiceResult(
            raw: trimmed,
            candidates: candidates,
            nbest: hypotheses,
            status: "ready"
        )
        statusMessage = "Ready — switch to ClarityIME keyboard"
        partialText = trimmed
        isListening = false
    }
}
