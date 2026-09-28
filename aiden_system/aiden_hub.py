#!/data/data/com.termux/files/usr/bin/python3

import os
import json
import subprocess
from datetime import datetime

HOME = os.path.expanduser("~")
SYSTEM = os.path.join(HOME, "aiden_system")

FILES = {
    "memory": os.path.join(SYSTEM, "aiden_memory.json"),
    "bootstrap": os.path.join(SYSTEM, "memory", "bootstrap.json"),
    "index": os.path.join(SYSTEM, "memory", "memory_index.json"),
    "wov_memory": os.path.join(HOME, "wov_core", "wov_core", "data", "memory.json"),
    "history": os.path.join(SYSTEM, "memory", "hub_history.json"),
}

def load(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print("[AIDEN] Ошибка:", path, e)
    return default

def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def status():
    print("\n[AIDEN HUB]")
    print("Пользователь: Вовчик")

    boot = load(FILES["bootstrap"], {})
    print("Модулей:", len(boot.get("modules", [])))
    print("Документов:", len(boot.get("projects", {})))

    idx = load(FILES["index"], {})
    if isinstance(idx, dict):
        print("Индекс загружен")

    mem = load(FILES["memory"], {})
    if isinstance(mem, dict):
        print("AIDEN memory:", len(mem), "записей")

    wov = load(FILES["wov_memory"], [])
    print("WOV memory:", len(wov), "записей")

    print("Время:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()

def remember(text):
    mem = load(FILES["memory"], {})
    if not isinstance(mem, dict):
        mem = {}

    mem["last_command"] = text
    mem["last_update"] = datetime.now().isoformat()

    save(FILES["memory"], mem)

    history = load(FILES["history"], [])
    if not isinstance(history, list):
        history = []

    history.append({
        "time": datetime.now().isoformat(),
        "command": text
    })

    save(FILES["history"], history[-1000:])

def projects():
    boot = load(FILES["bootstrap"], {})

    print("\n[AIDEN] ПРОЕКТЫ")

    modules = boot.get("modules", [])
    docs = boot.get("projects", {})

    print("Модулей:", len(modules))
    print("Документов:", len(docs))

    for path in modules[:30]:
        print("  ", path)

    if len(modules) > 30:
        print("  ... ещё", len(modules) - 30)

def modules():
    boot = load(FILES["bootstrap"], {})
    items = boot.get("modules", [])

    print("\n[AIDEN] МОДУЛИ:", len(items))

    for path in items[:50]:
        print(path)

    if len(items) > 50:
        print("... ещё", len(items) - 50)

def search(term):
    print("\n[AIDEN] ПОИСК:", term)

    indexes = [
        FILES["index"],
        FILES["bootstrap"],
    ]

    found = set()

    for path in indexes:
        data = load(path, {})

        text = json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )

        if term.lower() in text.lower():
            found.add(path)

    for path in found:
        print("[FOUND]", path)

    if not found:
        print("[AIDEN] В индексах не найдено.")

def main():
    print("======================================")
    print("          AIDEN HUB")
    print("======================================")
    print("[AIDEN] Единое ядро управления")
    print("[AIDEN] Память подключается")
    print("[AIDEN] WOV-CORE обнаружен")
    print("[AIDEN] Bootstrap обнаружен")
    print("[AIDEN] Индекс обнаружен")
    print()
    print("Команды:")
    print("  статус")
    print("  память")
    print("  проекты")
    print("  модули")
    print("  поиск <слово>")
    print("  сохрани <текст>")
    print("  aiden")
    print("  выход")
    print()

    while True:
        try:
            cmd = input("AIDEN> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[AIDEN] Завершение.")
            break

        if not cmd:
            continue

        low = cmd.lower()

        if low in ("выход", "exit", "quit"):
            print("[AIDEN] Завершение.")
            break

        elif low in ("статус", "status"):
            status()

        elif low in ("память", "memory"):
            status()

        elif low in ("проекты", "projects"):
            projects()

        elif low in ("модули", "modules"):
            modules()

        elif low.startswith("поиск "):
            search(cmd[6:].strip())

        elif low.startswith("сохрани "):
            remember(cmd[8:].strip())
            print("[AIDEN] Сохранено.")

        elif low == "aiden":
            target = os.path.join(
                HOME,
                "wov_core",
                "aiden_core",
                "aiden_core",
                "aiden.py"
            )

            if os.path.exists(target):
                subprocess.run(
                    ["python", target],
                    cwd=HOME
                )
            else:
                print("[AIDEN] Основное ядро не найдено.")

        else:
            remember(cmd)
            print("[AIDEN] Команда сохранена.")
            print("[AIDEN] Для работы с системой используй: статус / память / проекты / модули")

if __name__ == "__main__":
    main()
