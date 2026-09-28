import os
import json

HOME = os.path.expanduser("~")

TEXT_EXT = (
    ".py", ".txt", ".md", ".json",
    ".yaml", ".yml", ".ini", ".cfg",
    ".sh", ".log", ".csv"
)

SKIP_DIRS = {
    ".git",
    "__pycache__",
    "venv",
    "venv_aiden",
    "node_modules",
    ".cache"
}

memory = {
    "files": {}
}

print("[AIDEN] Сканирование...")

for root, dirs, files in os.walk(HOME):

    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

    for file in files:

        path = os.path.join(root, file)

        if not file.lower().endswith(TEXT_EXT):
            continue

        try:
            if os.path.getsize(path) > 1024 * 1024:
                continue

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                memory["files"][path] = f.read()

        except Exception:
            pass

outfile = os.path.join(HOME, "aiden_system", "aiden_memory.json")

with open(outfile, "w", encoding="utf-8") as f:
    json.dump(memory, f, ensure_ascii=False, indent=2)

print()
print("[OK] Готово.")
print("Файлов:", len(memory["files"]))
print("Память:", outfile)
