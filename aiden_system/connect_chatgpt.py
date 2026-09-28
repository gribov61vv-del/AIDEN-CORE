import os
import json
import requests

CFG=os.path.expanduser("~/aiden_system/config.json")

if os.path.exists(CFG):
    api=json.load(open(CFG))["api"]
else:
    api=input("Введите OpenAI API Key: ").strip()
    os.makedirs(os.path.dirname(CFG),exist_ok=True)
    json.dump({"api":api},open(CFG,"w"))

print("[AIDEN] ChatGPT подключён.")

while True:

    q=input("Вы> ")

    if q.lower() in ("exit","выход","quit"):
        break

    r=requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization":"Bearer "+api,
            "Content-Type":"application/json"
        },
        json={
            "model":"gpt-5.5",
            "input":q
        },
        timeout=120
    )

    if r.status_code!=200:
        print(r.text)
        continue

    data=r.json()

    try:
        print("\nAIDEN>",data["output"][0]["content"][0]["text"])
    except Exception:
        print(data)
