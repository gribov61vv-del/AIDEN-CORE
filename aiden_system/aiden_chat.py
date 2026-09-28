#!/data/data/com.termux/files/usr/bin/python3

import os
import json
import requests

HOME = os.path.expanduser("~")
CFG = os.path.join(HOME, "aiden_system", "config.json")
HISTORY = os.path.join(HOME, "aiden_system", "memory", "chat_history.json")

def load_key():
    with open(CFG, "r", encoding="utf-8") as f:
        data = json.load(f)
    key = data.get("api")
    if not key:
        raise RuntimeError("API key отсутствует в config.json")
    return key

def load_history():
    try:
        with open(HISTORY, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_history(data):
    os.makedirs(os.path.dirname(HISTORY), exist_ok=True)
    with open(HISTORY, "w", encoding="utf-8") as f:
        json.dump(data[-100:], f, ensure_ascii=False, indent=2)

def ask(text):
    key = load_key()
    hist = load_history()

    messages = [{
        "role": "system",
        "content": (
            "Ты — ChatGPT внутри локального AIDEN HUB. "
            "Пользователь — Вовчик. "
            "Отвечай естественно и по существу."
        )
    }]

    for item in hist[-20:]:
        messages.append({"role": "user", "content": item["user"]})
        messages.append({"role": "assistant", "content": item["assistant"]})

    messages.append({"role": "user", "content": text})

    model = os.environ.get("AIDEN_MODEL", "gpt-5.6")

    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": messages
        },
        timeout=120
    )

    data = r.json()

    if r.status_code != 200:
        return "[OPENAI ERROR] " + json.dumps(data, ensure_ascii=False)

    answer = data["choices"][0]["message"]["content"]

    hist.append({
        "user": text,
        "assistant": answer
    })

    save_history(hist)

    return answer

if __name__ == "__main__":
    print("[AIDEN] ChatGPT-мост запущен.")
    print("[AIDEN] Ключ берётся из config.json.")
    print("[AIDEN] История подключена.")
    print()

    while True:
        try:
            q = input("Вы> ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if q.lower() in ("выход", "exit", "quit"):
            break

        if q:
            print("\nAIDEN>", ask(q), "\n")
