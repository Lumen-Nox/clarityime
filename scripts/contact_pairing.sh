#!/usr/bin/env bash
# ClarityIME contact pairing — export/import via local core API
# Usage:
#   ./scripts/contact_pairing.sh export Sam [out.json]
#   ./scripts/contact_pairing.sh import bundle.json
set -euo pipefail
CORE="${CLARITYIME_CORE:-http://127.0.0.1:17800}"
cmd="${1:-}"
name="${2:-}"
out="${3:-}"

case "$cmd" in
  export)
    [[ -n "$name" ]] || { echo "usage: $0 export NAME [OUT.json]" >&2; exit 1; }
    enc=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$name'))")
    json=$(curl -sf "$CORE/v1/contacts/export?name=$enc")
    if [[ -n "$out" ]]; then
      printf '%s\n' "$json" > "$out"
      echo "exported -> $out"
    else
      printf '%s\n' "$json"
    fi
    ;;
  import)
    path="${2:-}"
    [[ -n "$path" && -f "$path" ]] || { echo "usage: $0 import PATH.json" >&2; exit 1; }
    curl -sf -X POST "$CORE/v1/contacts/import" \
      -H "Content-Type: application/json" \
      --data-binary @"$path" >/dev/null
    echo "imported from $path"
    ;;
  *)
    echo "usage: $0 export NAME [OUT] | import PATH" >&2
    exit 1
    ;;
esac
