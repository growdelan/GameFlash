#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

"$repo_root/scripts/check-context-size.sh"

if ! command -v uv >/dev/null 2>&1; then
    echo "Błąd: uv nie jest dostępny. Zainstaluj uv zgodnie z README.md." >&2
    exit 1
fi

if [ -d tests ]; then
    echo '+ uv run python -m unittest discover -s tests -p "test_*.py"'
    uv run python -m unittest discover -s tests -p "test_*.py"
else
    echo 'Brak katalogu tests/ — pominięto unittest discover.'
fi

# Dodaj tutaj jawne komendy lint, typecheck lub build po skonfigurowaniu projektu.
