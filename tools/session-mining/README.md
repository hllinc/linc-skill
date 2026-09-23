# session-mining

从本机 AI 编码助手的会话记录里抽出**你本人的发言**，供后续蒸馏工作方法。三个脚本，全部只读，输出到你指定目录。

| 脚本 | 来源 | 说明 |
|---|---|---|
| `extract_transcripts.py` | Claude Code `~/.claude/projects/*/*.jsonl`、Codex `~/.codex/sessions/**/*.jsonl`、Cursor `~/.cursor/projects/*/agent-transcripts/*/*.jsonl` | Cursor transcript 文件只覆盖近几个月；Claude Code 默认 30 天清理 |
| `extract_cursor_state.py` | Cursor 状态库 `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb` | 覆盖 Cursor 全部历史（本机可达两年）；用 workspaceStorage 映射工作区；只读打开 |
| `scan_leaks.sh` | 任意目录 | 提炼稿或归档外发前扫凭据与内部标识 |

用法：

```bash
python3 extract_transcripts.py OUT_DIR
python3 extract_cursor_state.py OUT_DIR --since 2025-09-01 --until 2026-03-12
./scan_leaks.sh OUT_DIR
```

输出格式：每个会话一个 `=====` 块头（工具、日期、工作区、轮数），下面是 `--- U1`、`--- U2` 编号的原话；另有 `index.tsv`。分块 ≈150KB，便于交给子代理分段深读。

蒸馏时的规则（来自实际教训）：每条规则至少三条不同日期的原话支撑；单句只能当例子；被质疑时先扩大证据面再改；子代理的摘引是线索，落地前回原文核语境。
