#!/data/data/com.termux/files/usr/bin/python3

import os
import json
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "aiden_system")

NODES = os.path.join(BASE, "nodes", "local_nodes.json")
HISTORY = os.path.join(BASE, "memory", "dispatcher_history.json")

def load(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def nodes():
    return load(NODES, {}).get("nodes", [])

def route(q):
    ql = q.lower()

    if any(x in ql for x in (
        "память", "вспомни", "история", "сохрани"
    )):
        return "MEMORY"

    if any(x in ql for x in (
        "код", "python", "wov", "проект",
        "модуль", "скрипт", "termux"
    )):
        return "WOV-CORE"

    return "LOCAL"

def history(q, r):
    h = load(HISTORY, [])

    h.append({
        "time": datetime.now().isoformat(),
        "query": q,
        "route": r
    })

    save(HISTORY, h[-5000:])

def local_answer(q, r):
    if r == "MEMORY":
        h = load(HISTORY, [])
        return (
            "[AIDEN/MEMORY] "
            f"История доступна: {len(h)} записей."
        )

    if r == "WOV-CORE":
        count = len([
            n for n in nodes()
            if n.get("type") == "WOV-CORE"
        ])

        return (
            "[AIDEN/WOV-CORE] "
            f"Доступно локальных WOV-узлов: {count}."
        )

    return (
        "[AIDEN/LOCAL] "
        "Запрос принят локальным вычислительным слоем."
    )

def main():
    print("======================================")
    print("          AIDEN ASK ENGINE")
    print("======================================")
    print("[OK] Локальный исполнитель активен.")
    print("[OK] Внешний AI необязателен.")
    print()

    while True:
        try:
            q = input("Вы> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[AIDEN] Выход.")
            break

        if not q:
            continue

        if q.lower() in ("выход", "exit", "quit"):
            break

        r = route(q)
        history(q, r)

        print()
        print("Маршрут:", r)
        print(local_answer(q, r))
        print()

if __name__ == "__main__":
    main()
