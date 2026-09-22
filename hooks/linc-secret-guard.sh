#!/usr/bin/env bash
# PreToolUse(Bash|Write|Edit): 命令或写入内容含明文凭据时拒绝（linc-skill §9 凭据不进对话/仓库）。
input=$(cat)
text=$(printf '%s' "$input" | jq -r '[.tool_input.command, .tool_input.content, .tool_input.new_string] | map(select(. != null)) | join("\n")')
[ -z "$text" ] && exit 0
pat='ghp_[A-Za-z0-9]{30,}|gho_[A-Za-z0-9]{30,}|glpat-[A-Za-z0-9_-]{15,}|glsa_[A-Za-z0-9_-]{20,}|npm_[A-Za-z0-9]{30,}|sk-ant-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{40,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|xox[bap]-[0-9A-Za-z-]{20,}|eyJhbGciOi[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}|(mongodb(\+srv)?|postgres(ql)?|mysql|redis|amqp)://[^:/@\s]+:[^@\s]{6,}@|-----BEGIN [A-Z ]*PRIVATE KEY-----'
hit=$(printf '%s' "$text" | grep -Eo "$pat" | head -1 || true)
if [ -n "$hit" ]; then
  kind=$(printf '%s' "$hit" | cut -c1-12)
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"linc-skill: 检测到疑似明文凭据（%s…），命令/文件里只放变量名与存放位置，值放 .env 或 secret（§9）"}}\n' "$kind"
fi
exit 0
