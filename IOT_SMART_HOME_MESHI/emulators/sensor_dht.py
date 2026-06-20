import paho.mqtt.client as mqtt
import time
import random
import json

BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "smarthome/sensor/dht"
CONTROL_TOPIC = "smarthome/control/dht"

sensor_active = True

def on_message(client, userdata, msg):
    """Handle MQTT control messages for DHT sensor."""
    global sensor_active
    command = msg.payload.decode("utf-8").strip().lower()
    if command == "off":
        sensor_active = False
        print("❌ DHT Sensor TURNED OFF")
    elif command == "on":
        sensor_active = True
        print("✅ DHT Sensor TURNED ON")

client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.subscribe(CONTROL_TOPIC)

print("📡 DHT Sensor Emulator Started - Listening for ON/OFF commands...")

try:
    while True:
        client.loop_start()
        if sensor_active:
            temperature = round(random.uniform(18, 35), 2)
            humidity = round(random.uniform(30, 80), 2)
            payload = json.dumps({"temperature": temperature, "humidity": humidity})
            client.publish(TOPIC, payload)
            print(f"📤 Sent: {payload} to {TOPIC}")
        time.sleep(5)

except KeyboardInterrupt:
    print("\n❌ Stopping DHT Sensor Emulator...")
    client.disconnect()
