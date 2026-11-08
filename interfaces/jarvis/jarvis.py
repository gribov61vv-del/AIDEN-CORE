#!/usr/bin/env python3
"""JARVIS V5: local voice interface. TRIAD is primary; PIKACHU is separate."""
import datetime, json, urllib.error, urllib.parse, urllib.request, webbrowser
import speech_recognition as sr
import pyttsx3

WOV_URL = "http://127.0.0.1:8000"
PIKACHU_URL = "http://127.0.0.1:8001"
HTTP_TIMEOUT = 8
engine = pyttsx3.init()

def talk(text):
    text = str(text)
    print("JARVIS:", text)
    engine.say(text)
    engine.runAndWait()

def request_json(url, payload=None, timeout=HTTP_TIMEOUT):
    if payload is None:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
    else:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data,
            headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def ask_triad(prompt):
    try:
        result = request_json(WOV_URL + "/ask", {"message": prompt})
        return str(result.get("answer") or "TRIAD вернул пустой ответ.")
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
        return "WOV/TRIAD недоступен; фиктивный ответ не подставлялся: " + str(exc)

def ask_pikachu(prompt):
    try:
        query = urllib.parse.urlencode({"q": prompt})
        result = request_json(PIKACHU_URL + "/ask?" + query)
        return "PIKACHU (экспериментально): " + str(result.get("answer", "пустой ответ"))
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
        return "PIKACHU недоступен: " + str(exc)

def system_status():
    parts = []
    for name, url in (("WOV/TRIAD", WOV_URL + "/ping"), ("PIKACHU", PIKACHU_URL + "/ping")):
        try:
            data = request_json(url, timeout=3)
            parts.append(name + ": online (" + str(data.get("status", "ok")) + ")")
        except Exception as exc:
            parts.append(name + ": offline (" + str(exc) + ")")
    return ". ".join(parts)

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("JARVIS слушает...")
        recognizer.adjust_for_ambient_noise(source, duration=0.4)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=12)
        except sr.WaitTimeoutError:
            return ""
    try:
        text = recognizer.recognize_google(audio, language="ru-RU")
        print("Распознано:", text)
        return text.strip()
    except sr.UnknownValueError:
        talk("Не расслышал.")
    except sr.RequestError as exc:
        talk("Ошибка распознавания: " + str(exc))
    return ""

def execute_command(command):
    raw = command.strip()
    low = raw.lower().replace("ё", "е")
    if not low: return True
    if low in ("выход", "завершить", "стоп jarvis"):
        talk("JARVIS завершает работу.")
        return False
    if "привет" in low:
        talk("Здарова. На связи.")
    elif low in ("время", "который час", "сколько времени"):
        talk("Сейчас " + datetime.datetime.now().strftime("%H:%M"))
    elif low in ("браузер", "открой браузер"):
        webbrowser.open("https://www.google.com")
        talk("Открываю браузер.")
    elif low in ("статус", "проверь связь", "статус системы"):
        talk(system_status())
    elif low.startswith("пикачу "):
        talk(ask_pikachu(raw.split(" ", 1)[1]))
    else:
        prompt = raw.split(" ", 1)[1] if low.startswith("триад ") else raw
        talk(ask_triad(prompt))
    return True

def main():
    print("JARVIS V5: запросы идут в WOV/TRIAD; команда «Пикачу ...» вызывает PIKACHU.")
    talk("JARVIS готов. Основной маршрут — TRIAD.")
    while True:
        phrase = listen()
        if phrase and not execute_command(phrase): break

if __name__ == "__main__":
    main()
