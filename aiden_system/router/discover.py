#!/data/data/com.termux/files/usr/bin/python3

import os
import json
import hashlib
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "aiden_system")
CFG = os.path.join(BASE, "router", "config.json")
OUT = os.path.join(BASE, "nodes", "local_nodes.json")

SKIP = {
    ".git", ".venv", "venv", "__pycache__",
    "node_modules", ".cache"
}

TARGETS = {
    "AIDEN": [
        "aiden.py", "aiden_core.py",
        "aiden_hub.py", "aiden_engineer.py"
    ],
    "WOV-CORE": [
        "core.py", "modules.py", "api.py",
        "wov_core.py"
    ],
    "MEMORY": [
        "aiden_memory.json",
        "memory.json",
        "bootstrap.json",
        "memory_index.json"
    ],
    "CHATGPT": [
        "chatgpt_module.py",
        "connect_chatgpt.py"
    ],
    "PROJECT": [
        "buildozer.spec",
        "start.sh"
    ]
}

def classify(name):
    low = name.lower()

    for group, names in TARGETS.items():
        if low in {x.lower() for x in names}:
            return group

    return None

def fingerprint(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except:
        return None

nodes = []
seen = set()

roots = [
    os.path.join(HOME, "wov_core"),
    os.path.join(HOME, "aiden_system")
]

for root in roots:
    if not os.path.exists(root):
        continue

    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP]

        for name in files:
            group = classify(name)

            if not group:
                continue

            path = os.path.join(current, name)

            if path in seen:
                continue

            seen.add(path)

            nodes.append({
                "name": name,
                "type": group,
                "path": path,
                "sha256": fingerprint(path),
                "size": os.path.getsize(path),
                "discovered": datetime.now().isoformat()
            })

os.makedirs(os.path.dirname(OUT), exist_ok=True)

data = {
    "system": "AIDEN",
    "mode": "local",
    "created": datetime.now().isoformat(),
    "nodes": nodes
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

try:
    with open(CFG, "r", encoding="utf-8") as f:
        cfg = json.load(f)
except:
    cfg = {
        "mode": "auto",
        "local": True,
        "providers": [],
        "nodes": []
    }

cfg["nodes"] = [
    {
        "name": n["name"],
        "type": n["type"],
        "path": n["path"]
    }
    for n in nodes
]

with open(CFG, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)

print()
print("======================================")
print("       AIDEN LOCAL DISCOVERY")
print("======================================")
print("[OK] Сканирование завершено.")
print("[OK] Найдено узлов:", len(nodes))
print()

groups = {}
for n in nodes:
    groups.setdefault(n["type"], []).append(n)

for group, items in groups.items():
    print(f"[{group}] {len(items)}")

print()
for n in nodes:
    print(f"  [{n['type']}] {n['path']}")

print()
print("[AIDEN] Узлы записаны:")
print(OUT)
print()
