# actuators_module.py
import time
from machine import Pin, PWM

# Pines y componentes
led_azul = Pin(14, Pin.OUT)
led_tapado = Pin(18, Pin.OUT)
led_impresion = Pin(19, Pin.OUT)
buzzer = Pin(20, Pin.OUT)
switch_motor = Pin(16, Pin.IN, Pin.PULL_UP)

servo_llenado = PWM(Pin(15)); servo_llenado.freq(50)
servo_tapado = PWM(Pin(10)); servo_tapado.freq(50)

# Motor L298N
in1 = Pin(6, Pin.OUT)
in2 = Pin(7, Pin.OUT)
ena = PWM(Pin(8)); ena.freq(1000)

def mover_servo(pos, servo_obj):
    min_duty = 1638
    max_duty = 8192
    duty = int(min_duty + (pos / 180) * (max_duty - min_duty))
    servo_obj.duty_u16(duty)

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