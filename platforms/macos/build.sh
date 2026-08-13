#!/usr/bin/env bash
# Build ClarityIME macOS InputMethodKit app (Release → dist/ClarityIME.app)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

DERIVED="$SCRIPT_DIR/build/DerivedData"
DIST="$SCRIPT_DIR/dist"
PROJECT="$SCRIPT_DIR/ClarityIME.xcodeproj"

if ! command -v xcodegen >/dev/null 2>&1; then
  echo "xcodegen not found. Install: brew install xcodegen"
  exit 1
fi

if ! xcodebuild -version >/dev/null 2>&1; then
  echo "Xcode command-line tools required. Install Xcode from the App Store."
  exit 1
fi

echo "→ xcodegen generate"
xcodegen generate

SIGN_ID="${CODE_SIGN_IDENTITY:-}"
BUILD_ARGS=(
  -project "$PROJECT"
  -scheme ClarityIME
  -configuration Release
  -derivedDataPath "$DERIVED"
  build
)

if [[ -n "$SIGN_ID" ]]; then
  BUILD_ARGS+=(CODE_SIGN_IDENTITY="$SIGN_ID")
else
  BUILD_ARGS+=(CODE_SIGN_IDENTITY=- CODE_SIGNING_ALLOWED=NO)
fi

echo "→ xcodebuild ${BUILD_ARGS[*]}"
xcodebuild "${BUILD_ARGS[@]}"

APP="$(find "$DERIVED" -path '*/Build/Products/Release/ClarityIME.app' -type d | head -1)"
if [[ -z "$APP" || ! -d "$APP" ]]; then
  echo "Build failed: ClarityIME.app not found under $DERIVED"
  exit 1
fi

mkdir -p "$DIST"
rm -rf "$DIST/ClarityIME.app"
cp -R "$APP" "$DIST/"
echo "Built → $DIST/ClarityIME.app"

if [[ "${RUN_TESTS:-0}" == "1" ]]; then
  echo "→ xcodebuild test"
  xcodebuild \
    -project "$PROJECT" \
    -scheme ClarityIME \
    -configuration Debug \
    -derivedDataPath "$DERIVED" \
    test \
    CODE_SIGN_IDENTITY=- CODE_SIGNING_ALLOWED=NO
fi
