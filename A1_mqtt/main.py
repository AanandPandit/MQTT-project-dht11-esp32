import network
import time
from machine import Pin
import ujson as json
from umqtt.simple import MQTTClient
import dht

# WiFi credentials
wifi_ssid = 'test'
wifi_password = 'qwertyuiop'

# MQTT broker configuration
mqtt_broker = '91.121.93.94'  # Replace with your MQTT broker address
mqtt_port = 1883
# mqtt_user = 'admin device'
# mqtt_password = 'password23'

# LED pins
led_pins = {
    'led1': 19,    # gpio pin 19
    'led2': 18,    # gpio pin 18
    'led3': 5      # gpio pin 5
}

# Initialize the DHT11 sensor
dht_pin = 23  # Replace with the GPIO pin number connected to the DHT11 sensor
try:
    dht_sensor = dht.DHT11(Pin(dht_pin))
except Exception as e:
    print("DHT11 sensor not found:", e)
    dht_sensor = None

def connect_to_wifi(ssid, password):
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(ssid, password)

    print("Connecting to WiFi...")
    while not station.isconnected():
        print("Connecting to WiFi...", end="\n")
        time.sleep(1)
    print("\nConnected to WiFi")

def sub_cb(topic, msg):
    try:
        led_name = topic.decode('utf-8')
        led_pin = led_pins.get(led_name)
        if led_pin is not None:
            led_state = int(msg.decode('utf-8'))
            if led_state in [0, 1]:
                led = Pin(led_pin, Pin.OUT)
                led.value(led_state)
                print(f"LED {led_name} set to {led_state}")
            else:
                print("Invalid LED state. Use 0 or 1.")
        else:
            print("Invalid LED name")
    except Exception as e:
        print("Error:", e)

connect_to_wifi(wifi_ssid, wifi_password)

client = MQTTClient("esp32_client", mqtt_broker, port=mqtt_port)
client.set_callback(sub_cb)

while True:
    try:
        client.connect()
        client.subscribe(b"led1")
        client.subscribe(b"led2")
        client.subscribe(b"led3")
        print("Connected to MQTT broker. Waiting for messages...")

        last_dht_publish_time = 0
        while True:
            current_time = time.time()

            if current_time - last_dht_publish_time >= 2 and dht_sensor is not None:
                # Read DHT11 sensor data
                try:
                    dht_sensor.measure()
                    temperature = dht_sensor.temperature()
                    humidity = dht_sensor.humidity()

                    # Publish DHT11 data to MQTT
                    client.publish(b"dht11/temperature", bytes(str(temperature), 'utf-8'))
                    print("Temperature:", temperature)
                    client.publish(b"dht11/humidity", bytes(str(humidity), 'utf-8'))
                    print("Humidity:", humidity)

                    last_dht_publish_time = current_time
                except Exception as e:
                    print("Error reading DHT sensor:", e)

            client.check_msg()  # Check for MQTT messages

    except KeyboardInterrupt:
        print("\nDisconnecting from MQTT broker...")
        client.disconnect()
        print("Disconnected.")
        break
    except Exception as e:
        print("Error:", e)
        time.sleep(5)  # Wait for a few seconds before attempting to reconnect
