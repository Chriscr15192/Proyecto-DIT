# rfid_module.py
from machine import Pin, SPI
from mfrc522 import MFRC522
import time
import ujson

class RFIDReader:
    def __init__(self, mqtt_client, topic_acceso):
        # Pines del RFID
        self.lector = MFRC522(spi_id=0, sck=2, miso=4, mosi=3, cs=1, rst=0)
        # LEDs
        self.rojo = Pin(13, Pin.OUT)
        self.verde = Pin(12, Pin.OUT)
        # MQTT
        self.mqtt_client = mqtt_client
        self.topic_acceso = topic_acceso
        # UID autorizados
        self.TARJETA = 2864276003
        self.LLAVERO = 2798854115

    def leer(self):
        """Lee el RFID y devuelve el UID y estado"""
        self.lector.init()
        (stat, tag_type) = self.lector.request(self.lector.REQIDL)
        if stat == self.lector.OK:
            (stat, uid) = self.lector.SelectTagSN()
            if stat == self.lector.OK:
                identificador = int.from_bytes(bytes(uid), "little", False)
                if identificador in [self.TARJETA]:
                    estado = "ACCESO_CONCEDIDO"
                    self.rojo.value(0)
                    self.verde.value(1)
                else:
                    estado = "ACCESO_DENEGADO"
                    self.rojo.value(1)
                    self.verde.value(0)

                # Publicar mensaje en MQTT
                mensaje = ujson.dumps({
                    "uid": identificador,
                    "estado": estado
                })
                self.mqtt_client.publish(self.topic_acceso, mensaje)
                print(f"UID leído: {identificador}, Estado: {estado}")
                print("Publicado en MQTT:", mensaje)

                time.sleep(2)
                self.rojo.value(0)
                self.verde.value(0)
                return identificador, estado
        return None, None
