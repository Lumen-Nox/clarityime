// swift-tools-version: 5.9
//
// ClarityIME macOS InputMethodKit app is built via Xcode (xcodegen + xcodebuild).
// InputMethodKit apps cannot be packaged as a plain SwiftPM executable.
//
// Workflow:
//   cd platforms/macos
//   xcodegen generate          # → ClarityIME.xcodeproj
//   ./build.sh                 # or open in Xcode
//
// This manifest exists so Swift tooling / CI can resolve the package name and
// run logic-only tests if extracted helpers are moved here in the future.

import PackageDescription

let package = Package(
    name: "ClarityIMEPlatform",
    platforms: [.macOS(.v13)],
    products: [],
    targets: []
)
