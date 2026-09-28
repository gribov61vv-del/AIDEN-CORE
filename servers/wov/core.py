import time
import random

def log(msg):
    print(f"[WOV-CORE] {msg}")

def init():
    log("Инициализация наноструктур...")
    time.sleep(1)
    log("Диагностика гиперболоида...")
    time.sleep(1)
    log("Балансировка энергетического поля...")
    time.sleep(1)

def precharge():
    log("Предзарядка ядра...")
    for i in range(3):
        log(f"  Заряд {i+1}/3")
        time.sleep(1)

def focus():
    log("Фокусировка энергии в квантовой камере...")
    time.sleep(2)

def launch():
    log("Запуск резонанса...")
    time.sleep(1)
    log("Активация тройного кольца стабилизации...")
    time.sleep(1)
    log("Формирование первичного защитного барьера...")
    time.sleep(1)

def sync():
    log("Синхронизация с биометрией пилота...")
    time.sleep(1)
    log("Ядро вышло на стабильный режим ⚡🔥")

def sustain():
    log("Поддержка режима ядра активирована.")
    while True:
        temp = round(random.uniform(36.5, 42.0), 2)
        energy = random.randint(87, 100)
        log(f"Состояние стабильное | Температура: {temp}°C | Энергия: {energy}%")
        time.sleep(10)

if __name__ == "__main__":
    init()
    precharge()
    focus()
    launch()
    sync()
    sustain()
