#!/usr/bin/env python
# curl https://get.pimoroni.com/bme680 | bash
# sudo pip install paho-mqtt
# crontab: */5 *   * * * root python /home/pi/bme680_mqtt.py

import bme680
# import context  # Ensures paho is in PYTHONPATH
import paho.mqtt.publish as publish
import time
import os
import platform
hostname = platform.node()

try:
    sensor = bme680.BME680()
except OSError:
    sensor = bme680.BME680(i2c_addr=bme680.constants.I2C_ADDR_SECONDARY)
sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)
sensor.set_gas_status(bme680.DISABLE_GAS_MEAS)

sensor.set_temp_offset(0)
if sensor.get_sensor_data():
    output = "{0:.2f} C, {1:.2f} hPa, {2:.3f} %RH".format(
        sensor.data.temperature, sensor.data.pressure, sensor.data.humidity)
    print(output)
    print("")

    publish.multiple([
        {'topic': "bme680/"+hostname+"/temperature",
         'payload': sensor.data.temperature},
        {'topic': "bme680/"+hostname+"/pressure", 'payload': sensor.data.pressure},
        {'topic': "bme680/"+hostname+"/humidity", 'payload': sensor.data.humidity},
    ], hostname=os.environ["MQTT_BROKER"])

if True:  # time.localtime().tm_min < 59:
    print("Time to do air quality gas measurement...")
    sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
    sensor.set_gas_heater_temperature(320)
    sensor.set_gas_heater_duration(150)
    sensor.select_gas_heater_profile(0)

    # start_time and curr_time ensure that the
    # burn_in_time (in seconds) is kept track of.

    start_time = time.time()
    curr_time = time.time()
    burn_in_time = 240

    burn_in_data = []

    # Collect gas resistance burn-in values, then use the average
    # of the last 50 values to set the upper limit for calculating
    # gas_baseline.
    print('Collecting gas resistance burn-in data for 4 mins\n')
    while curr_time - start_time < burn_in_time:
        curr_time = time.time()
        if sensor.get_sensor_data() and sensor.data.heat_stable:
            gas = sensor.data.gas_resistance
            burn_in_data.append(gas)
            print('Value @ {0} is Gas: {1} Ohms'.format(
                curr_time - start_time, gas))
            time.sleep(1)

    gas_baseline = sum(burn_in_data[-50:]) / 50.0
    # https://forums.pimoroni.com/t/bme680-observed-gas-ohms-readings/6608/13
    gas_baseline_lo = 100000
    gas_baseline_hi = 350000
    # Set the humidity baseline to 40%, an optimal indoor humidity.
    hum_baseline = 40.0

    # This sets the balance between humidity and gas reading in the
    # calculation of air_quality_score (25:75, humidity:gas)
    hum_weighting = 0.25

    print('Gas baseline: {0} Ohms, humidity baseline: {1:.2f} %RH\n'.format(
        gas_baseline,
        hum_baseline))

    if sensor.get_sensor_data() and sensor.data.heat_stable:
        gas = sensor.data.gas_resistance
        gas_offset = gas_baseline - gas

        hum = sensor.data.humidity
        hum_offset = hum - hum_baseline

        # Calculate hum_score as the distance from the hum_baseline.
        if hum_offset > 0:
            hum_score = (100 - hum_baseline - hum_offset)
            hum_score /= (100 - hum_baseline)
            hum_score *= (hum_weighting * 100)

        else:
            hum_score = (hum_baseline + hum_offset)
            hum_score /= hum_baseline
            hum_score *= (hum_weighting * 100)

        # Calculate gas_score as the distance from the gas_baseline.
        # Too low resistive = perfect score
        if gas < gas_baseline_lo:
            gas_score = 100 - (hum_weighting * 100)
        # Too high resistive = too much gunk in the air = worst score zero
        elif gas > gas_baseline_hi:
            gas_score = 0
        else:
            # work out percentage in range between high and low
            gas_score = ((gas-gas_baseline_lo) / (gas_baseline_hi-gas_baseline_lo))
            # scale score to include weighting of humidity
            gas_score *= (100 - (hum_weighting * 100))

        # Calculate air_quality_score.
        air_quality_score = hum_score + gas_score

        print('Gas: {0:.2f} Ohms,humidity: {1:.2f} %RH,air quality: {2:.2f}'.format(
            gas,
            hum,
            air_quality_score))

        publish.multiple(
            [
                {'topic': "bme680/"+hostname+"/gas_resistance", "payload": round(gas,2)},
                {'topic': "bme680/"+hostname+"/air_quality",
                 "payload": round(air_quality_score,2)}
            ], hostname=os.environ["MQTT_BROKER"])