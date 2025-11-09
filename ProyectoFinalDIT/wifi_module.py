# wifi_module.py
import network
import time

SSID = "victorcha"
PASSWORD = "2686069010"

def conectar_internet():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("Conectando a Wi-Fi...")
        sta_if.active(True)
        sta_if.connect(SSID, PASSWORD)
        while not sta_if.isconnected():
            time.sleep(1)
    print("✅ Conectado a Wi-Fi:", sta_if.ifconfig()[0])
