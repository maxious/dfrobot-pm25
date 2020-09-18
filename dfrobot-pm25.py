# -*- coding: utf-8 -*-
# https://wiki.dfrobot.com/PM2.5_laser_dust_sensor_SKU_SEN0177
import serial
ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout = 1500 #set the Timeout to 1500ms, longer than the data transmission periodic time of the sensor
)
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(26,GPIO.OUT)
print("Sensor on")
GPIO.output(26,GPIO.HIGH)

buf = []
readings = 0
def parseBuf(buf):
	#print([x.hex() for x in buf])
	thebuf = [int.from_bytes(x,'little') for x in buf[1:]]
	#print(thebuf)
	receiveSum=0;
	leng = 31
	i = 0
	while i<(leng-2):
		receiveSum=receiveSum+thebuf[i]
		i += 1
	receiveSum=receiveSum + 0x42; #calculate sum
	#print(receiveSum)
	if receiveSum == ((thebuf[leng-2]<<8)+thebuf[leng-1]):  #check the serial data
		PM01Val=((thebuf[3]<<8) + thebuf[4]) # count PM1.0 value of the air detector module
		PM2_5Val=((thebuf[5]<<8) + thebuf[6]) # count PM2.5 value of the air detector module
		PM10Val=((thebuf[7]<<8) + thebuf[8]) # count PM10 value of the air detector module
		print(PM01Val, PM2_5Val, PM10Val)
	else:
		print("bad receive sum", receiveSum, "!=",  ((thebuf[leng-2]<<8)+thebuf[leng-1]))
while readings < 4:
	buf.append(ser.read())
	if buf[0].hex() != "42":
		#print([x.hex() for x in buf])
		buf = []
	if len(buf) > 31:
		parseBuf(buf)
		readings += 1
		buf = []
print("Sensor off")
GPIO.output(26,GPIO.LOW)
