#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

warnings=0

status_max_lines="${STATUS_MAX_LINES:-150}"
status_max_bytes="${STATUS_MAX_BYTES:-12288}"
roadmap_max_lines="${ROADMAP_MAX_LINES:-350}"
roadmap_max_bytes="${ROADMAP_MAX_BYTES:-30720}"
spec_max_lines="${SPEC_MAX_LINES:-500}"
spec_max_bytes="${SPEC_MAX_BYTES:-40960}"

check_file() {
    local file="$1"
    local max_lines="$2"
    local max_bytes="$3"
    local lines bytes

    if [ ! -f "$file" ]; then
        echo "INFO: brak $file — pominięto kontrolę rozmiaru."
        return
    fi

    lines="$(wc -l < "$file" | tr -d ' ')"
    bytes="$(wc -c < "$file" | tr -d ' ')"

    if [ "$lines" -gt "$max_lines" ] || [ "$bytes" -gt "$max_bytes" ]; then
        echo "WARNING: $file ma ${lines} linii i ${bytes} B; zalecany limit to ${max_lines} linii / ${max_bytes} B."
        warnings=$((warnings + 1))
    else
        echo "OK: $file — ${lines}/${max_lines} linii, ${bytes}/${max_bytes} B."
    fi
}

check_file STATUS.md "$status_max_lines" "$status_max_bytes"
check_file ROADMAP.md "$roadmap_max_lines" "$roadmap_max_bytes"
check_file spec.md "$spec_max_lines" "$spec_max_bytes"

if [ "$warnings" -gt 0 ]; then
    echo "Kontekst wymaga uporządkowania: użyj \$codex-flow-compact-context."
else
    echo "Rozmiary głównych plików kontekstu są w zalecanych granicach."
fi

# Limity są ostrzegawcze; ich przekroczenie nie blokuje pozostałych walidacji.
exit 0
