import paho.mqtt.client as mqtt
import sqlite3
import json

# MQTT connection settings
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "smarthome/#"  # Subscribe to all topics under smarthome/

# Database setup
DB_NAME = "iot_database.db"

def init_db():
    """Initialize the database and create a table if not exists."""
    conn = sqlite3.connect("data_manager/iot_database.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS sensor_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        topic TEXT,
                        message TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                      )''')
    conn.commit()
    conn.close()

def save_to_db(topic, message):
    """Save received MQTT messages to the database."""
    try:
        conn = sqlite3.connect("data_manager/iot_database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sensor_data (topic, message) VALUES (?, ?)", (topic, message))
        conn.commit()
        conn.close()
        print(f"✅ Saved to database: {topic} - {message}")
    except Exception as e:
        print(f"❌ Error saving data: {e}")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        client.subscribe(TOPIC)
    else:
        print("❌ Connection failed")

import json

def on_message(client, userdata, msg):
    """Handle incoming MQTT messages."""
    topic = msg.topic
    message = msg.payload.decode("utf-8").strip()  # הסרת רווחים ריקים
    print(f"📩 Received message: {message} from topic: {topic}")

    if not message:
        print("⚠️ Empty message received. Ignoring.")
        return

    # שמירה למסד הנתונים
    save_to_db(topic, message)

    try:
        # טיפול בהודעות ON/OFF
        if message == "ON":
            print("✅ Relay turned ON")
        elif message == "OFF":
            print("✅ Relay turned OFF")
        elif message.startswith("{") and message.endswith("}"):  # רק אם זה JSON
            data = json.loads(message)
            if "temperature" in data:
                temp = data["temperature"]
                if temp > 30:
                    print(f"⚠️ WARNING: High Temperature Detected! {temp}°C 🔥")
                elif temp < 20:
                    print(f"⚠️ ALERT: Low Temperature Detected! {temp}°C ❄️")
        else:
            print(f"⚠️ Non-JSON message received: {message}")
    except json.JSONDecodeError:
        print(f"❌ Error processing JSON: Invalid format - {message}")
    except Exception as e:
        print(f"❌ Unexpected error processing message: {e}")

# Initialize database
init_db()

# Setup MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)

# Start MQTT loop
print("📡 Listening for messages...")
client.loop_forever()
