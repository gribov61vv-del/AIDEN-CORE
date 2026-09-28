#!/data/data/com.termux/files/usr/bin/python3

import os
import json
import requests

CFG = os.path.expanduser("~/aiden_system/config.json")

# Приоритет: сначала актуальные GPT-5.x,
# затем более старые доступные модели.
PREFERRED = [
    "gpt-5.6",
    "gpt-5.5",
    "gpt-5.4",
    "gpt-5.3",
    "gpt-5",
    "gpt-4.1",
    "gpt-4o-mini",
]

def key():
    with open(CFG, encoding="utf-8") as f:
        return json.load(f)["api"]

def available_models(k):
    r = requests.get(
        "https://api.openai.com/v1/models",
        headers={"Authorization": "Bearer " + k},
        timeout=30
    )
    r.raise_for_status()
    return {x["id"] for x in r.json().get("data", [])}

def choose(k):
    available = available_models(k)

    # Сначала пытаемся найти предпочтительную модель.
    for model in PREFERRED:
        if model in available:
            return model

    # Если названия поменялись —
    # ищем любую современную GPT-модель.
    candidates = sorted(
        m for m in available
        if m.startswith(("gpt-", "o"))
    )

    if candidates:
        return candidates[0]

    raise RuntimeError("У API-ключа нет подходящей текстовой модели.")

def ask(text):
    k = key()
    model = choose(k)

    print("[AIDEN] Модель:", model)

    r = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": "Bearer " + k,
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "input": text
        },
        timeout=120
    )

    data = r.json()

    if r.status_code != 200:
        return "[OPENAI ERROR] " + json.dumps(data, ensure_ascii=False)

    # Responses API
    if data.get("output_text"):
        return data["output_text"]

    # Запасной разбор
    try:
        return data["output"][0]["content"][0]["text"]
    except Exception:
        return json.dumps(data, ensure_ascii=False)

def main():
    print("[AIDEN] MODEL ROUTER АКТИВЕН")
    print("[AIDEN] Модель выбирается автоматически.")
    print("[AIDEN] Жёсткой привязки к одной модели нет.")
    print()

    while True:
        try:
            q = input("Вы> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[AIDEN] Выход.")
            break

        if q.lower() in ("выход", "exit", "quit"):
            break

        if q:
            try:
                print("\nAIDEN>", ask(q), "\n")
            except Exception as e:
                print("[AIDEN ERROR]", e)

if __name__ == "__main__":
    main()
