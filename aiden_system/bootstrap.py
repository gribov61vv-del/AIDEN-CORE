import os
import json

HOME = os.path.expanduser("~")

MEM = {
    "user": "Вовчик",
    "projects": {},
    "modules": [],
    "logs": []
}

for root, dirs, files in os.walk(HOME):
    if ".git" in root:
        continue

    for f in files:
        path = os.path.join(root, f)

        if f.endswith((".py", ".pyx", ".sh")):
            MEM["modules"].append(path)

        if f.endswith((".json", ".txt", ".md")):
            MEM["projects"][f] = path

with open(os.path.join(HOME,
                       "aiden_system",
                       "memory",
                       "bootstrap.json"),
          "w",
          encoding="utf-8") as fp:
    json.dump(MEM, fp, ensure_ascii=False, indent=2)

print("[AIDEN] Bootstrap создан.")
print("[AIDEN] Модулей:", len(MEM["modules"]))
print("[AIDEN] Документов:", len(MEM["projects"]))
