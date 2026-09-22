#!/usr/bin/env bash
# PreToolUse(Bash): 拦 linc-skill §3.2/§3.8 禁止的 git 动作。
# deny: 无 lease 的强推；删除含 release 的远端分支。 ask: 在默认/集成分支上 commit 或 merge；branch -D / worktree remove --force。
input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')
[ -z "$cmd" ] && exit 0
case "$cmd" in *git*) ;; *) exit 0;; esac
deny() { printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"linc-skill: %s"}}\n' "$1"; exit 0; }
ask()  { printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"linc-skill: %s"}}\n' "$1"; exit 0; }
if printf '%s' "$cmd" | grep -Eq 'git[^|;&]*push[^|;&]*(\s-f\b|\s--force\b)' && ! printf '%s' "$cmd" | grep -Eq -- '--force-with-lease'; then
  deny "禁止无 lease 的强推（§3.8）；需要时用 --force-with-lease=<branch>:<远端oid>"
fi
if printf '%s' "$cmd" | grep -Eq 'git[^|;&]*push[^|;&]*(--delete|:)[^|;&]*[Rr][Ee][Ll][Ee][Aa][Ss][Ee]'; then
  deny "含 release 的分支绝不自动删除（§3.9）"
fi
if printf '%s' "$cmd" | grep -Eq 'git[^|;&]*(branch\s+-D\b|worktree\s+remove[^|;&]*--force)'; then
  ask "强制删分支/worktree，先确认已集成（§3.9 用 branch -d / remove 不带 force）"
fi
if printf '%s' "$cmd" | grep -Eq 'git[^|;&]*\b(commit|merge)\b'; then
  dir=$(printf '%s' "$cmd" | grep -Eo 'git\s+-C\s+\S+' | head -1 | awk '{print $3}')
  br=$(git ${dir:+-C "$dir"} rev-parse --abbrev-ref HEAD 2>/dev/null || true)
  case "$br" in main|master|develop) ask "当前在 $br 分支上 $(printf '%s' "$cmd" | grep -Eo '\b(commit|merge)\b' | head -1)；默认/集成分支只做基线，改动应在功能分支+worktree（§3.2），合并走平台（§3.8）";; esac
fi
exit 0
