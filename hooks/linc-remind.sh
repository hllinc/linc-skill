#!/usr/bin/env bash
# UserPromptSubmit: 每条提示注入一行提醒，让 agent 先按 linc-skill 分类定档。
cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"linc-skill: 研发类任务先按 SKILL.md §0 分类并定风险档（低/中/高），按档位决定读多少手册、做哪些步骤；未加载 linc-skill 先用 Skill 工具加载。"}}
JSON
