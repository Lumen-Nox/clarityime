import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var speech: SpeechRecognizerService
    @State private var showSettings = false
    private let store = SharedStore.shared

    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                statusCard
                transcriptCard
                micButton
                candidatesPreview
                keyboardHint
            }
            .padding()
            .navigationTitle("ClarityIME")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showSettings = true
                    } label: {
                        Image(systemName: "gearshape")
                    }
                }
            }
            .sheet(isPresented: $showSettings) {
                SettingsView()
            }
            .onAppear {
                speech.requestAuthorization()
                let flushed = FeedbackSync.flushPending()
                if flushed > 0 {
                    store.setVoiceStatus("Synced \(flushed) queued feedback(s)")
                }
            }
        }
    }

    private var statusCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("Host · Voice → Keyboard", systemImage: "waveform")
                .font(.headline)
            Text("Mode: \(store.audienceMode)\(store.defaultContact.map { " · \($0)" } ?? "")")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Text(speech.statusMessage.isEmpty ? store.voiceStatusMessage : speech.statusMessage)
                .font(.caption)
                .foregroundStyle(speech.isListening ? .orange : .secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }

    private var transcriptCard: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Transcript")
                .font(.caption)
                .foregroundStyle(.secondary)
            ScrollView {
                Text(displayTranscript)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .textSelection(.enabled)
            }
            .frame(minHeight: 80, maxHeight: 140)
        }
        .padding()
        .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 12))
    }

    private var displayTranscript: String {
        if !speech.partialText.isEmpty { return speech.partialText }
        if !store.voiceRawText.isEmpty { return store.voiceRawText }
        return "Tap 🎤 and speak. Clarified candidates sync to the ClarityIME keyboard."
    }

    private var micButton: some View {
        Button {
            speech.toggleListening()
        } label: {
            ZStack {
                Circle()
                    .fill(speech.isListening ? Color.red.opacity(0.85) : Color.accentColor)
                    .frame(width: 88, height: 88)
                    .shadow(radius: speech.isListening ? 8 : 4)
                Image(systemName: speech.isListening ? "stop.fill" : "mic.fill")
                    .font(.system(size: 32))
                    .foregroundStyle(.white)
            }
        }
        .disabled(!speech.isAuthorized)
        .accessibilityLabel(speech.isListening ? "Stop listening" : "Start voice input")
    }

    private var candidatesPreview: some View {
        Group {
            if store.voiceCandidates.isEmpty && speech.lastCandidates.isEmpty {
                Text("Candidates appear here after speech, and in the keyboard extension.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            } else {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Latest candidates (shared with keyboard)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    ForEach(Array(activeCandidates.enumerated()), id: \.offset) { _, item in
                        HStack {
                            Text("[\(item.label)]")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                            Text(item.text)
                                .font(.subheadline)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
            }
        }
    }

    private var activeCandidates: [ClarifyCandidate] {
        speech.lastCandidates.isEmpty ? store.voiceCandidates : speech.lastCandidates
    }

    private var keyboardHint: some View {
        Text("Switch to **ClarityIME** keyboard → tap a candidate to insert into the active field.")
            .font(.footnote)
            .foregroundStyle(.secondary)
            .multilineTextAlignment(.center)
    }
}

#Preview {
    ContentView()
        .environmentObject(SpeechRecognizerService())
}
