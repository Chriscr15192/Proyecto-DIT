import time
import ujson
import ubinascii
import machine
from machine import Pin, PWM
import dht
from simple import MQTTClient
from rfid_module import RFIDReader
import network

# ---------------- WIFI ----------------
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

conectar_internet()

# ---------------- MQTT ----------------
BROKER = "def64533ae474dc39aaf1132f8b1ceda.s1.eu.hivemq.cloud"
PORT = 8883
MQTT_USER = "Christian"
MQTT_PASS = "Christian123"
TOPIC_ESTADO = b"linea_refrescos/estado"

id_cliente_mqtt = ubinascii.hexlify(machine.unique_id())
cliente_mqtt = MQTTClient(
    client_id=id_cliente_mqtt,
    server=BROKER,
    port=PORT,
    user=MQTT_USER,
    password=MQTT_PASS,
    ssl=True,
    ssl_params={"server_hostname": BROKER}
)
cliente_mqtt.connect()
print("✅ Conectado al broker MQTT")

# ---------------- COMPONENTES ----------------
led_azul = Pin(14, Pin.OUT)
switch_motor = Pin(16, Pin.IN, Pin.PULL_UP)
dht_sensor = dht.DHT22(Pin(17))
servo_llenado = PWM(Pin(15)); servo_llenado.freq(50)
servo_tapado = PWM(Pin(10)); servo_tapado.freq(50)
led_tapado = Pin(18, Pin.OUT)
led_impresion = Pin(19, Pin.OUT)
buzzer = Pin(20, Pin.OUT); buzzer.value(0)
trig = Pin(22, Pin.OUT)
echo = Pin(21, Pin.IN)

# Pines L298N
in1 = Pin(6, Pin.OUT)
in2 = Pin(7, Pin.OUT)
ena = PWM(Pin(8)); ena.freq(1000)

# ---------------- RFID ----------------
rfid = RFIDReader(cliente_mqtt, b"rfid/acceso")

# ---------------- FUNCIONES ----------------
def mover_servo(pos, servo_obj):
    min_duty = 1638
    max_duty = 8192
    duty = int(min_duty + (pos / 180) * (max_duty - min_duty))
    servo_obj.duty_u16(duty)

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

def motor_adelante(max_duty=20000, step=500, delay=0.05):
    in1.value(1); in2.value(0)
    for d in range(0, max_duty, step):
        ena.duty_u16(d)
        time.sleep(delay)

def motor_parar(step=500, delay=0.05):
    current_duty = ena.duty_u16()
    for d in range(current_duty, -1, -step):
        ena.duty_u16(d)
        time.sleep(delay)
    in1.value(0); in2.value(0); ena.duty_u16(0)

def sonar_buzzer(tiempo=1):
    buzzer.value(1)
    time.sleep(tiempo)
    buzzer.value(0)

def leer_temperatura():
    try:
        dht_sensor.measure()
        return dht_sensor.temperature()
    except Exception as e:
        print("⚠️ Error leyendo DHT22:", e)
        return None

def enviar_estado_mqtt(motor, acceso, temperatura, distancia, botellas, etapa):
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
    cliente_mqtt.publish(TOPIC_ESTADO, payload)
    print("📤 Enviado MQTT:", payload)

# ---------------- ESTADOS ----------------
motor_encendido = False
acceso_valido = False
contador_botellas = 0
ultimo_contador = 0
ultimo_motor = False
ultimo_temp_alerta = False
TEMP_ALERTA = 20  # °C

print("🔄 Sistema de línea de producción iniciado...\n")

# ---------------- LOOP PRINCIPAL ----------------
while True:
    uid, estado = rfid.leer()
    if estado == "ACCESO_CONCEDIDO" and not acceso_valido:
        acceso_valido = True
        print("✅ Acceso concedido")

    # Control motor manual
    if acceso_valido and switch_motor.value() == 0 and not motor_encendido:
        print("🟩 Motor encendido")
        motor_encendido = True
        motor_adelante()
        led_azul.value(1)
    elif switch_motor.value() == 1 and motor_encendido:
        print("🟥 Motor detenido")
        motor_parar()
        motor_encendido = False
        led_azul.value(0)
        sonar_buzzer(0.5)

    temperatura = leer_temperatura()
    distancia = medir_distancia()
    etapa = "ESPERA"
    temp_alerta = temperatura is not None and temperatura > TEMP_ALERTA

    # Detectar botella y ejecutar ciclo solo si hay botella y motor encendido
    if motor_encendido and distancia is not None and distancia < 10:
        print("📦 Botella detectada")
        etapa = "LLENADO"

        # Llenado
        mover_servo(90, servo_llenado)
        time.sleep(1)
        mover_servo(0, servo_llenado)

        # Tapado
        etapa = "TAPADO"
        led_tapado.value(1)
        for ang in range(0, 181, 20):
            mover_servo(ang, servo_tapado)
            time.sleep(0.05)
        for ang in range(180, -1, -20):
            mover_servo(ang, servo_tapado)
            time.sleep(0.05)
        led_tapado.value(0)

        # Impresión
        etapa = "IMPRESION"
        led_impresion.value(1)
        time.sleep(1)
        led_impresion.value(0)
        sonar_buzzer(0.3)

        # Contador de botellas
        contador_botellas += 1
        print(f"🍾 Botellas completadas: {contador_botellas}")

    # Enviar MQTT solo si hay cambios
    enviar = False
    if contador_botellas != ultimo_contador:
        enviar = True
        ultimo_contador = contador_botellas
    if motor_encendido != ultimo_motor:
        enviar = True
        ultimo_motor = motor_encendido
    if temp_alerta != ultimo_temp_alerta:
        enviar = True
        ultimo_temp_alerta = temp_alerta

    if enviar:
        enviar_estado_mqtt(
            motor_encendido,
            acceso_valido,
            temperatura,
            distancia,
            contador_botellas,
            etapa
        )

    time.sleep(0.5)



