from typing import Dict, List, Any, Union

import requests
import paho.mqtt.publish as publish
import os
import platform

hostname = platform.node()


def mqtt_publish(readings):
    if not os.environ.get("MQTT_BROKER"):
        print("no MQTT broker defined")
        return

    mqtt_messages: List[Dict[str, Union[str, Any]]] = [
        {'topic': "sen0177/" + hostname + "/pm1", 'payload': readings['PM01']},
        {'topic': "sen0177/" + hostname + "/pm2_5", 'payload': readings['PM2_5']},
        {'topic': "sen0177/" + hostname + "/pm10", 'payload': readings['PM10']},
        {'topic': "bme680/" + hostname + "/temperature", 'payload': readings['temperature']},
        {'topic': "bme680/" + hostname + "/pressure", 'payload': readings['pressure']},
        {'topic': "bme680/" + hostname + "/humidity", 'payload': readings['humidity']}]
    publish.multiple(mqtt_messages, hostname=os.environ["MQTT_BROKER"])


# https://github.com/pimoroni/enviroplus-python/blob/master/examples/luftdaten.py
# Get Raspberry Pi serial number to use as ID
def _get_serial_number():
    with open('/proc/cpuinfo', 'r') as f:
        for line in f:
            if line[0:6] == 'Serial':
                return line.split(":")[1].strip()


def luftdaten_publish(readings):
    # https://github.com/opendata-stuttgart/meta/wiki/APIs#api-luftdateninfo
    values = {}
    sensor_id = "raspi-" + _get_serial_number()
    software_version = "github:maxious/dfrobot-pm25 0.0.1"
    luftdaten_api_url = "https://api.sensor.community/v1/push-sensor-data/"

    values["temperature"] = "{:.2f}".format(readings['temperature'])
    values["pressure"] = "{:.2f}".format(readings['pressure'] * 100)
    values["humidity"] = "{:.2f}".format(readings['humidity'])
    values["P2"] = str(readings['PM2_5'])
    values["P1"] = str(readings['PM10'])

    pm_values = dict(i for i in values.items() if i[0].startswith("P"))
    temp_values = dict(i for i in values.items() if not i[0].startswith("P"))

    pm_values_json = [{"value_type": key, "value": val} for key, val in pm_values.items()]
    temp_values_json = [{"value_type": key, "value": val} for key, val in temp_values.items()]

    resp_1 = requests.post(
        luftdaten_api_url,
        json={
            "software_version": software_version,
            "sensordatavalues": pm_values_json
        },
        headers={
            "X-PIN": "1",
            "X-Sensor": sensor_id,
            "Content-Type": "application/json",
            "cache-control": "no-cache"
        }
    )

    resp_2 = requests.post(
        luftdaten_api_url,
        json={
            "software_version": software_version,
            "sensordatavalues": temp_values_json
        },
        headers={
            "X-PIN": "11",
            "X-Sensor": sensor_id,
            "Content-Type": "application/json",
            "cache-control": "no-cache"
        }
    )

    if resp_1.ok and resp_2.ok:
        return True
    else:
        return False
