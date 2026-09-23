#!/usr/bin/env bash
# Scan a directory for credentials and internal identifiers before sharing distilled material. Exit 1 on hits.
dir="${1:-.}"
pat='ghp_[A-Za-z0-9]{30,}|gho_[A-Za-z0-9]{30,}|glpat-[A-Za-z0-9_-]{15,}|glsa_[A-Za-z0-9_-]{20,}|npm_[A-Za-z0-9]{30,}|sk-ant-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|xox[bap]-[0-9A-Za-z-]{20,}|eyJhbGciOi[A-Za-z0-9_-]{20,}|(mongodb(\+srv)?|postgres(ql)?|mysql|redis|amqp)://[^:/@[:space:]]+:[^@[:space:]]{6,}@|-----BEGIN [A-Z ]*PRIVATE KEY-----'
extra="${LEAK_EXTRA_PATTERN:-}"   # e.g. company/product/person names, domains
hits=$(grep -rEn "$pat" "$dir" 2>/dev/null | head -20)
[ -n "$extra" ] && hits="$hits"$'\n'"$(grep -rEni "$extra" "$dir" 2>/dev/null | head -20)"
hits=$(printf '%s' "$hits" | sed '/^$/d')
if [ -n "$hits" ]; then echo "$hits"; echo "LEAK CHECK: hits found"; exit 1; fi
echo "LEAK CHECK: clean"
