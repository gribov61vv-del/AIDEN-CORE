#!/data/data/com.termux/files/usr/bin/python3

import os
import json
import requests
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "aiden_system")
CFG = os.path.join(BASE, "router", "provider.json")
OPENAI_CFG = os.path.join(BASE, "config.json")
LOG = os.path.join(BASE, "logs", "provider.log")

# Модели ставим в порядке предпочтения.
# Если первой нет — пробуем следующую.
PREFERRED = [
    "gpt-4.1",
    "gpt-4o",
    "o4-mini",
    "o3-mini",
    "gpt-4o-mini",
    "gpt-5-nano-2025-08-07",
]

def log(text):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(
            "[%s] %s\n" %
            (datetime.now().isoformat(), text)
        )

def get_key():
    try:
        with open(OPENAI_CFG, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("api")
    except Exception as e:
        log("config error: %s" % e)
        return None

def get_models(key):
    try:
        r = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": "Bearer " + key},
            timeout=15
        )

        if r.status_code != 200:
            log("models HTTP %s" % r.status_code)
            return []

        data = r.json()

        return sorted(
            x.get("id")
            for x in data.get("data", [])
            if x.get("id")
        )

    except Exception as e:
        log("models error: %s" % e)
        return []

def choose_model(models):
    available = set(models)

    for model in PREFERRED:
        if model in available:
            return model

    # Резерв: любая доступная chat/gpt модель
    candidates = [
        x for x in models
        if x.startswith(("gpt-", "o1", "o3", "o4"))
        and "audio" not in x
        and "transcribe" not in x
        and "tts" not in x
    ]

    return candidates[0] if candidates else None

def ask_openai(prompt):
    key = get_key()

    if not key:
        return {
            "ok": False,
            "error": "API key не найден"
        }

    models = get_models(key)

    if not models:
        return {
            "ok": False,
            "error": "Нет доступных моделей"
        }

    model = choose_model(models)

    if not model:
        return {
            "ok": False,
            "error": "Не найден подходящий исполнитель"
        }

    log("selected model: %s" % model)

    try:
        r = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": "Bearer " + key,
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "input": prompt
            },
            timeout=60
        )

        if r.status_code != 200:
            log("request HTTP %s: %s" % (r.status_code, r.text[:500]))
            return {
                "ok": False,
                "error": r.text
            }

        data = r.json()

        text = data.get("output_text")

        if text:
            return {
                "ok": True,
                "provider": "openai",
                "model": model,
                "answer": text
            }

        # Резервный разбор Responses API
        parts = []

        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    parts.append(content.get("text", ""))

        text = "\n".join(parts).strip()

        if text:
            return {
                "ok": True,
                "provider": "openai",
                "model": model,
                "answer": text
            }

        return {
            "ok": False,
            "error": "API вернул ответ без текста"
        }

    except Exception as e:
        log("request exception: %s" % e)
        return {
            "ok": False,
            "error": str(e)
        }

def main():
    print("======================================")
    print("       AIDEN PROVIDER MANAGER")
    print("======================================")
    print("[AIDEN] Провайдеры отделены от ядра.")
    print("[AIDEN] Модель выбирается автоматически.")
    print("[AIDEN] Жёсткой привязки к одной модели нет.")
    print()

    while True:
        try:
            q = input("AIDEN> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[AIDEN] Выход.")
            break

        if not q:
            continue

        if q.lower() in ("выход", "exit", "quit"):
            break

        if q.lower() in ("модели", "models"):
            key = get_key()

            if not key:
                print("[ERROR] API key не найден.")
                continue

            models = get_models(key)

            print("\nДоступно:", len(models))

            for m in models:
                print(" ", m)

            print()
            continue

        if q.lower() in ("статус", "status"):
            key = get_key()

            if not key:
                print("[AIDEN] API key отсутствует.")
                continue

            models = get_models(key)
            model = choose_model(models)

            print()
            print("[AIDEN] Provider: OPENAI")
            print("[AIDEN] API: OK")
            print("[AIDEN] Доступных моделей:", len(models))
            print("[AIDEN] Выбран исполнитель:", model)
            print()
            continue

        print("[AIDEN] Маршрут: EXTERNAL_PROVIDER")

        result = ask_openai(q)

        if result.get("ok"):
            print()
            print(
                "[AIDEN/%s/%s]" %
                (
                    result.get("provider"),
                    result.get("model")
                )
            )
            print(result["answer"])
            print()
        else:
            print()
            print("[AIDEN] Внешний исполнитель недоступен.")
            print("[AIDEN] Причина:", result.get("error"))
            print("[AIDEN] Ядро продолжает работать локально.")
            print()

if __name__ == "__main__":
    main()
