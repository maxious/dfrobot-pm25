import serial
import time
import input,output
import RPi.GPIO as GPIO

ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1500  # set the Timeout to 1500ms, longer than the data transmission periodic time of the sensor
)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(26, GPIO.OUT)
print("Sensor on")
GPIO.output(26, GPIO.HIGH)

# take some readings
buf = []
readings = []
while len(readings) < 4:
    buf.append(ser.read())
    if buf[0].hex() != "42":
        buf = []
    if len(buf) > 31:
        readings.append(input.parse_buf(buf))
        buf = []
        time.sleep(1)

print("Sensor off")
GPIO.output(26, GPIO.LOW)

meanReadings = input.meanReadings(readings)
publishedReadings = meanReadings + input.get_bme680_values()
output.mqtt_publish(publishedReadings)
output.luftdaten_publish(publishedReadings)