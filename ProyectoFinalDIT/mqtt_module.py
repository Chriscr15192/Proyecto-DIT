# mqtt_module.py
import ubinascii
import ujson
import machine
from simple import MQTTClient

BROKER = "def64533ae474dc39aaf1132f8b1ceda.s1.eu.hivemq.cloud"
PORT = 8883
MQTT_USER = "Christian"
MQTT_PASS = "Christian123"
TOPIC_ESTADO = b"linea_refrescos/estado"

def conectar_mqtt():
    id_cliente_mqtt = ubinascii.hexlify(machine.unique_id())
    cliente = MQTTClient(
        client_id=id_cliente_mqtt,
        server=BROKER,
        port=PORT,
        user=MQTT_USER,
        password=MQTT_PASS,
        ssl=True,
        ssl_params={"server_hostname": BROKER}
    )
    cliente.connect()
    print("✅ Conectado al broker MQTT")
    return cliente

def enviar_estado_mqtt(cliente, motor, acceso, temperatura, distancia, botellas, etapa):
    import time
    mensaje = {
        "motor_encendido": motor,
        "acceso_valido": acceso,
        "temperatura": temperatura,
        "distancia": distancia,
        "botella_detectada": botellas,
        "etapa": etapa,
        "timestamp": time.time()
    }
    payload = ujson.dumps(mensaje)
    cliente.publish(TOPIC_ESTADO, payload)
    print("📤 Enviado MQTT:", payload)
