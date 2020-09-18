# curl https://get.pimoroni.com/bme680 | bash
import bme680

import statistics


def parse_buf(buf):
    # print([x.hex() for x in buf])
    thebuf = [int.from_bytes(x, 'little') for x in buf[1:]]
    # print(thebuf)
    receiveSum = 0;
    leng = 31
    i = 0
    while i < (leng - 2):
        receiveSum = receiveSum + thebuf[i]
        i += 1
    receiveSum = receiveSum + 0x42  # calculate sum
    # print(receiveSum)
    if receiveSum == ((thebuf[leng - 2] << 8) + thebuf[leng - 1]):  # check the serial data
        PM01Val = ((thebuf[3] << 8) + thebuf[4])  # count PM1.0 value of the air detector module
        PM2_5Val = ((thebuf[5] << 8) + thebuf[6])  # count PM2.5 value of the air detector module
        PM10Val = ((thebuf[7] << 8) + thebuf[8])  # count PM10 value of the air detector module
        print(PM01Val, PM2_5Val, PM10Val)
        return {"PM01": PM01Val, "PM2_5": PM2_5Val, "PM!0": PM10Val}
    else:
        print("bad receive sum", receiveSum, "!=", ((thebuf[leng - 2] << 8) + thebuf[leng - 1]))
        return None


def meanReadings(readings):
    allReadings = {}
    meanReadings = {}
    for reading in readings:
        for k, v in reading.items():
            if k not in allReadings:
                allReadings[k] = []
            allReadings[k].append(v)
    for k, v in allReadings.items():
        meanReadings[k] = statistics.mean(v)
    return meanReadings


def get_bme680_values():
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
        return {"temperature": sensor.data.temperature,
                "pressure": sensor.data.pressure,
                "humidity": sensor.data.humidity}
    else:
        return None
