#!/data/data/com.termux/files/usr/bin/python3

import os
import json
import subprocess
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

def get_nodes():
    data = load(NODES, {})
    return data.get("nodes", [])

def record(command, route):
    history = load(HISTORY, [])
    history.append({
        "time": datetime.now().isoformat(),
        "command": command,
        "route": route
    })
    save(HISTORY, history[-2000:])

def status():
    nodes = get_nodes()

    groups = {}
    for n in nodes:
        groups.setdefault(n["type"], []).append(n)

    print()
    print("======================================")
    print("          AIDEN DISPATCHER")
    print("======================================")
    print("Локальных узлов:", len(nodes))

    for k, v in groups.items():
        print(f"{k}: {len(v)}")

    print()
    print("Маршрутизация:")
    print("  память      -> MEMORY")
    print("  проект      -> WOV-CORE")
    print("  вычисление  -> LOCAL")
    print("  внешний AI  -> PROVIDER")
    print()

def find_type(t):
    return [n for n in get_nodes() if n["type"] == t]

def route(cmd):
    low = cmd.lower()

    if any(x in low for x in [
        "память", "вспомни", "сохрани", "история"
    ]):
        return "MEMORY"

    if any(x in low for x in [
        "проект", "код", "python", "wov", "модуль"
    ]):
        return "WOV-CORE"

    return "LOCAL"

def main():
    print("======================================")
    print("        AIDEN AUTONOMOUS CORE")
    print("======================================")
    print("[OK] Диспетчер запущен.")
    print("[OK] Локальные узлы подключены.")
    print("[OK] OpenAI не является обязательным.")
    print()
    print("Команды:")
    print("  статус")
    print("  узлы")
    print("  выход")
    print()

    while True:
        try:
            cmd = input("Вовчик> ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not cmd:
            continue

        low = cmd.lower()

        if low in ("выход", "exit", "quit"):
            break

        if low in ("статус", "status"):
            status()
            continue

        if low in ("узлы", "nodes"):
            for n in get_nodes():
                print(
                    f"[{n['type']}] "
                    f"{n['path']}"
                )
            continue

        selected = route(cmd)

        record(cmd, selected)

        print()
        print("[AIDEN] Маршрут:", selected)

        if selected == "MEMORY":
            print("[AIDEN] Запрос направлен в слой памяти.")

        elif selected == "WOV-CORE":
            print("[AIDEN] Запрос направлен в WOV-CORE.")

        else:
            print("[AIDEN] Запрос обрабатывается локальным ядром.")

        print()

if __name__ == "__main__":
    main()
