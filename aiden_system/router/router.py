#!/data/data/com.termux/files/usr/bin/python3
import os
import json
import socket
import urllib.request
from datetime import datetime

BASE = os.path.expanduser("~/aiden_system")
CFG = os.path.join(BASE, "router", "config.json")
LOG = os.path.join(BASE, "logs", "router.log")

DEFAULT = {
    "mode": "auto",
    "providers": [],
    "nodes": [],
    "local": True
}

def load():
    try:
        with open(CFG, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        save(DEFAULT)
        return DEFAULT.copy()

def save(x):
    os.makedirs(os.path.dirname(CFG), exist_ok=True)
    with open(CFG, "w", encoding="utf-8") as f:
        json.dump(x, f, ensure_ascii=False, indent=2)

def log(x):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("[%s] %s\n" % (datetime.now().isoformat(), x))

def internet():
    try:
        urllib.request.urlopen("https://www.google.com/generate_204", timeout=3)
        return True
    except:
        return False

def status():
    c = load()
    print("\n========== AIDEN ROUTER ==========")
    print("Режим:", c.get("mode"))
    print("Локальный режим: ON" if c.get("local") else "OFF")
    print("Интернет:", "ON" if internet() else "OFF")
    print("Провайдеров:", len(c.get("providers", [])))
    print("Узлов:", len(c.get("nodes", [])))
    print("Телефон:", socket.gethostname())
    print("==================================\n")

def main():
    print("[AIDEN] Независимый вычислительный слой запущен.")
    print("[AIDEN] OpenAI не является ядром системы.")
    print("[AIDEN] Локальный режим готов.")
    print("[AIDEN] Команды: статус | режим auto | режим local | выход\n")

    while True:
        try:
            cmd = input("AIDEN-ROUTER> ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not cmd:
            continue

        low = cmd.lower()

        if low in ("выход", "exit", "quit"):
            break

        if low in ("статус", "status"):
            status()
            continue

        if low == "режим local":
            c = load()
            c["mode"] = "local"
            save(c)
            print("[AIDEN] Только локальное выполнение.")
            continue

        if low == "режим auto":
            c = load()
            c["mode"] = "auto"
            save(c)
            print("[AIDEN] Автоматический роутинг.")
            continue

        print("[AIDEN] Запрос принят роутером.")
        print("[AIDEN] Исполнители выбираются отдельно от ядра.")

if __name__ == "__main__":
    main()
