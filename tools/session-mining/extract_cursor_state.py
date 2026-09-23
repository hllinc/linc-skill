#!/usr/bin/env python3
"""Extract the user's own turns from Cursor's global state.vscdb (covers full history), attributing workspaces via workspaceStorage."""
import sqlite3, json, glob, re, sys, datetime, collections, argparse
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--since", default="2000-01-01"); ap.add_argument("--until", default="2100-01-01")
a=ap.parse_args(); OUT=Path(a.out); OUT.mkdir(parents=True, exist_ok=True); HOME=Path.home()
START=int(datetime.datetime.fromisoformat(a.since).timestamp()*1000); END=int(datetime.datetime.fromisoformat(a.until).timestamp()*1000)
ws_map={}
for wjson in glob.glob(str(HOME/"Library/Application Support/Cursor/User/workspaceStorage/*/workspace.json")):
    db=Path(wjson).parent/"state.vscdb"
    if not db.exists(): continue
    try:
        w=json.load(open(wjson)); ws=(w.get("folder") or w.get("workspace") or "?").replace("file://"+str(HOME)+"/","").replace("%20"," ")
        con=sqlite3.connect(f"file:{db}?mode=ro",uri=True); row=con.execute("select value from ItemTable where key='composer.composerData'").fetchone(); con.close()
        for c in (json.loads(row[0]).get("allComposers",[]) if row else []): ws_map[c.get("composerId")]=ws
    except Exception: pass
G=HOME/"Library/Application Support/Cursor/User/globalStorage/state.vscdb"
con=sqlite3.connect(f"file:{G}?mode=ro",uri=True)
rows=con.execute("select value from cursorDiskKV where key like 'composerData:%' and json_extract(value,'$.createdAt') between ? and ? and json_array_length(json_extract(value,'$.fullConversationHeadersOnly'))>0",(START,END)).fetchall()
def clean(t):
    t=re.sub(r"<user_query>\s*|\s*</user_query>","",t or ""); t=re.sub(r"<attached_files>.*?</attached_files>","[attached_files]",t,flags=re.S).strip()
    if t.startswith(("Briefly inform","Implement the plan as specified","Perform any necessary")): return ""
    return t[:1500]+(" …[truncated]" if len(t)>1500 else "")
sessions=[]
for (val,) in rows:
    d=json.loads(val); cid=d["composerId"]; hdrs=d.get("fullConversationHeadersOnly",[])
    ids=[h["bubbleId"] for h in hdrs if h.get("type")==1]; na=sum(1 for h in hdrs if h.get("type")==2); turns=[]
    for i in range(0,len(ids),200):
        keys=[f"bubbleId:{cid}:{b}" for b in ids[i:i+200]]
        got=dict(con.execute("select key,value from cursorDiskKV where key in (%s)"%",".join("?"*len(keys)),keys).fetchall())
        for k in keys:
            v=got.get(k)
            if v:
                try: t=clean(json.loads(v).get("text",""))
                except Exception: t=""
                if t: turns.append(t)
    if turns: sessions.append((datetime.datetime.fromtimestamp(d["createdAt"]/1000).strftime("%Y-%m-%d"), ws_map.get(cid,"?"), (d.get("name") or "")[:60], turns, na))
con.close(); sessions.sort()
buf=[];size=0;part=1
def flush():
    global buf,size,part
    if buf: (OUT/f"cursor-state-{part:02d}.md").write_text("".join(buf)); part+=1; buf=[]; size=0
with open(OUT/"index.tsv","w") as idx:
    for date,ws,name,turns,na in sessions:
        block=f"\n\n===== [cursor] {date} | {ws} | {name} | user_turns={len(turns)} assistant_msgs={na} =====\n"+"".join(f"\n--- U{i+1}\n{t}\n" for i,t in enumerate(turns))
        if size+len(block)>150000: flush()
        buf.append(block); size+=len(block); idx.write(f"cursor\t{date}\t{ws}\t{len(turns)}\t{na}\t{name}\n")
flush()
print("sessions",len(sessions),"turns",sum(len(s[3]) for s in sessions)); print(collections.Counter(s[1] for s in sessions).most_common(10))
