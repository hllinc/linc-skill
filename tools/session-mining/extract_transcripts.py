#!/usr/bin/env python3
"""Extract the user's own turns from Claude Code / Codex / Cursor transcript files into chunked markdown."""
import json, os, glob, re, sys, datetime, collections
from pathlib import Path
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
HOME = Path.home()

def clean(t):
    if not isinstance(t, str): return ""
    for p in ("<system-reminder", "<command-", "<local-command", "# AGENTS.md", "<INSTRUCTIONS>", "<environment_context", "<permissions", ">>> TRANSCRIPT", "The following is the Codex agent history", "Briefly inform the user", "Implement the plan as specified", "Perform any necessary"):
        if t.startswith(p): return ""
    t = re.sub(r"<system-reminder>.*?</system-reminder>", "", t, flags=re.S)
    t = re.sub(r"<user_query>\s*|\s*</user_query>", "", t)
    t = re.sub(r"<attached_files>.*?</attached_files>", "[attached_files]", t, flags=re.S)
    t = re.sub(r"<ide_selection>.*?</ide_selection>", "", t, flags=re.S).strip()
    return t[:1500] + (" …[truncated]" if len(t) > 1500 else "")

sessions = []
for f in glob.glob(str(HOME/".claude/projects/*/*.jsonl")):
    proj = Path(f).parent.name; turns=[]; na=0; date=None
    for line in open(f, errors="ignore"):
        try: o=json.loads(line)
        except: continue
        if o.get("type")=="user":
            date = date or (o.get("timestamp") or "")[:10]
            c=o.get("message",{}).get("content")
            parts = [c] if isinstance(c,str) else [p.get("text","") for p in c if isinstance(p,dict) and p.get("type")=="text"] if isinstance(c,list) else []
            turns += [t for t in map(clean, parts) if t]
        elif o.get("type")=="assistant": na+=1
    if turns: sessions.append(("claude-code", date or "?", proj, turns, na))
for f in glob.glob(str(HOME/".codex/sessions/**/*.jsonl"), recursive=True):
    meta=None; turns=[]; na=0
    for line in open(f, errors="ignore"):
        try: o=json.loads(line)
        except: continue
        if o.get("type")=="session_meta": meta=o["payload"]; continue
        if o.get("type")=="response_item" and o.get("payload",{}).get("role")=="user":
            turns += [t for t in (clean(p.get("text","")) for p in o["payload"].get("content",[]) or [] if p.get("type")=="input_text") if t]
        elif o.get("type")=="response_item" and o.get("payload",{}).get("role")=="assistant": na+=1
    if meta and meta.get("thread_source")=="user" and turns:  # skip guardian/subagent threads
        sessions.append(("codex", (meta.get("timestamp") or "?")[:10], (meta.get("cwd") or "?").replace(str(HOME)+"/",""), turns, na))
for f in glob.glob(str(HOME/".cursor/projects/*/agent-transcripts/*/*.jsonl")):
    proj = Path(f).parents[2].name; turns=[]; na=0
    for line in open(f, errors="ignore"):
        try: o=json.loads(line)
        except: continue
        c=o.get("message",{}).get("content",[])
        if o.get("role")=="user":
            turns += [t for t in (clean(p.get("text","")) for p in c if isinstance(p,dict) and p.get("type")=="text") if t]
        elif o.get("role")=="assistant": na+=1
    if turns: sessions.append(("cursor", datetime.datetime.fromtimestamp(os.stat(f).st_mtime).strftime("%Y-%m-%d"), proj, turns, na))

sessions.sort(key=lambda s:(s[0],s[1]))
by=collections.defaultdict(list)
for s in sessions: by[s[0]].append(s)
with open(OUT/"index.tsv","w") as idx:
    for tool, ss in by.items():
        buf=[]; size=0; part=1
        def flush():
            global buf,size,part
            if buf: (OUT/f"{tool}-{part:02d}.md").write_text("".join(buf)); part+=1; buf=[]; size=0
        for tool_,date,proj,turns,na in ss:
            block=f"\n\n===== [{tool_}] {date} | {proj} | user_turns={len(turns)} assistant_msgs={na} =====\n"+"".join(f"\n--- U{i+1}\n{t}\n" for i,t in enumerate(turns))
            if size+len(block)>150000: flush()
            buf.append(block); size+=len(block)
            idx.write(f"{tool_}\t{date}\t{proj}\t{len(turns)}\t{na}\t{turns[0][:80].replace(chr(10),' ')}\n")
        flush()
print({k:len(v) for k,v in by.items()}, "turns", sum(len(s[3]) for s in sessions))
