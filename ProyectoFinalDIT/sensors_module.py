# sensors_module.py
import time
import dht
from machine import Pin

# DHT22
dht_sensor = dht.DHT22(Pin(17))

# Sensor ultrasónico
trig = Pin(22, Pin.OUT)
echo = Pin(21, Pin.IN)

def leer_temperatura():
    try:
        dht_sensor.measure()
        return dht_sensor.temperature()
    except Exception as e:
        print("⚠️ Error leyendo DHT22:", e)
        return None

def medir_distancia(timeout=30000):
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    inicio = time.ticks_us()
    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), inicio) > timeout:
            return None
    inicio = time.ticks_us()
    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), inicio) > timeout:
            return None
        fin = time.ticks_us()
    duracion = fin - inicio
    return (duracion / 2) / 29.1
