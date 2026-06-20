import paho.mqtt.client as mqtt

# MQTT Broker configuration
BROKER = "test.mosquitto.org"
PORT = 1883

# List of topics to subscribe
TOPICS = [
    ("smarthome/sensor/dht", 0),
    ("smarthome/relay", 0),
    ("smarthome/actuator/button", 0),
    ("smarthome/control/dht", 0),
    ("smarthome/control/relay", 0),
]

def on_connect(client, userdata, flags, rc):
    """Handles the connection event to the MQTT broker."""
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        for topic in TOPICS:
            client.subscribe(topic)
            print(f"📡 Subscribed to {topic[0]}")
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    """Handles incoming messages from MQTT topics."""
    print(f"📩 Received message: {msg.topic} -> {msg.payload.decode()}")

def setup_mqtt_client():
    """Initialize and return an MQTT client."""
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    return client

if __name__ == "__main__":
    client = setup_mqtt_client()
    client.loop_forever()
