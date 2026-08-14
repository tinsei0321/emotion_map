# -*- coding: utf-8 -*-
"""一次性补丁：给 .claude/settings.json SessionStart 追加 sync_guard hook（幂等）。"""
import json

P = ".claude/settings.json"
with open(P, encoding="utf-8") as f:
    d = json.load(f)

ss = d["hooks"]["SessionStart"]
cmd = "python tools/sync_guard.py --mode status"
if not any(cmd in (h.get("command") or "") for h in ss):
    ss.append({"command": cmd})

with open(P, "w", encoding="utf-8", newline="\n") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.write("\n")

print("SessionStart hooks:", len(ss))
for h in ss:
    print(" -", h.get("command"))
