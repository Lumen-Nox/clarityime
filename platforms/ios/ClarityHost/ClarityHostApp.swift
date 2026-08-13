import SwiftUI

@main
struct ClarityHostApp: App {
    @StateObject private var speech = SpeechRecognizerService()
    @State private var showOnboarding = !SharedStore.shared.onboardingCompleted

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(speech)
                .fullScreenCover(isPresented: $showOnboarding) {
                    OnboardingView(isPresented: $showOnboarding)
                }
        }
    }
}
