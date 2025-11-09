# main.py
import time
from wifi_module import conectar_internet
from mqtt_module import conectar_mqtt, enviar_estado_mqtt
from sensors_module import leer_temperatura, medir_distancia
from actuators_module import (
    mover_servo, motor_adelante, motor_parar, sonar_buzzer,
    led_azul, led_tapado, led_impresion, servo_llenado, servo_tapado, switch_motor
)
from rfid_module import RFIDReader

# ---------------- INICIO ----------------
conectar_internet()
cliente_mqtt = conectar_mqtt()
rfid = RFIDReader(cliente_mqtt, b"rfid/acceso")

# ---------------- VARIABLES ----------------
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

    # Control manual de motor
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

    # Detección de botella
    if motor_encendido and distancia is not None and distancia < 10:
        print("📦 Botella detectada")
        etapa = "LLENADO"

        mover_servo(90, servo_llenado)
        time.sleep(1)
        mover_servo(0, servo_llenado)

        etapa = "TAPADO"
        led_tapado.value(1)
        for ang in range(0, 181, 20):
            mover_servo(ang, servo_tapado)
            time.sleep(0.05)
        for ang in range(180, -1, -20):
            mover_servo(ang, servo_tapado)
            time.sleep(0.05)
        led_tapado.value(0)

        etapa = "IMPRESION"
        led_impresion.value(1)
        time.sleep(1)
        led_impresion.value(0)
        sonar_buzzer(0.3)

        contador_botellas += 1
        print(f"🍾 Botellas completadas: {contador_botellas}")

    # Enviar solo si hay cambios
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
            cliente_mqtt,
            motor_encendido,
            acceso_valido,
            temperatura,
            distancia,
            contador_botellas,
            etapa
        )

    time.sleep(0.5)
