import sys
import json
import paho.mqtt.publish as publish
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLineEdit, QLabel
import paho.mqtt.client as mqtt


BROKER = "test.mosquitto.org"
PORT = 1883

CONTROL_TOPIC = "smarthome/control/dht"
SENSOR_TOPIC = "smarthome/sensor/dht"
DB_NAME = "data_manager/iot_database.db"

class SmartHomeGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Smart Home Data Viewer")
        self.setGeometry(100, 100, 500, 500)
        self.relay_state = "off"  # ברירת מחדל של ה-Relay

        layout = QVBoxLayout()

        # תצוגת הנתונים
        self.text_display = QTextEdit(self)
        self.text_display.setReadOnly(True)
        layout.addWidget(self.text_display)

        # כפתור רענון
        self.refresh_button = QPushButton("Refresh Data", self)
        self.refresh_button.clicked.connect(self.load_data)
        layout.addWidget(self.refresh_button)

        # כפתור Toggle Relay
        self.relay_button = QPushButton("Toggle Relay", self)
        self.relay_button.clicked.connect(self.toggle_relay)
        layout.addWidget(self.relay_button)

        # כפתור הפעלה/כיבוי של DHT
        self.toggle_sensor_button = QPushButton("Turn OFF Sensor", self)
        self.toggle_sensor_button.clicked.connect(self.toggle_sensor)
        layout.addWidget(self.toggle_sensor_button)

        # שדה קלט להזנת טמפרטורה ידנית
        self.temp_input = QLineEdit(self)
        self.temp_input.setPlaceholderText("Enter temperature (e.g., 25.5)")
        layout.addWidget(self.temp_input)

        # כפתור לשליחת טמפרטורה ידנית
        self.send_temp_button = QPushButton("Send Custom Temperature", self)
        self.send_temp_button.clicked.connect(self.send_custom_temperature)
        layout.addWidget(self.send_temp_button)

        self.setLayout(layout)
        self.sensor_on = True  # מצב חיישן התחלתי - דולק

        self.load_data()  # טעינת נתונים ראשונית

        # 🔹 התחברות ל-MQTT והאזנה לסטטוס ה-Relay 🔹
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.connect("test.mosquitto.org", 1883, 60)  # ודאי שזה אותו Broker של שאר הרכיבים
        self.mqtt_client.subscribe("smarthome/relay")  # מאזין לסטטוס ה-Relay
        self.mqtt_client.loop_start()

    def toggle_sensor(self):
        """Toggle the DHT sensor ON/OFF via MQTT."""
        if self.sensor_on:
            publish.single(CONTROL_TOPIC, "off", hostname=BROKER)
            self.toggle_sensor_button.setText("Turn ON Sensor")
            self.sensor_on = False
        else:
            publish.single(CONTROL_TOPIC, "on", hostname=BROKER)
            self.toggle_sensor_button.setText("Turn OFF Sensor")
            self.sensor_on = True
    
    def toggle_relay(self):
        """Send an MQTT 'toggle' command to the relay, similar to the button emulator."""
        try:
            client = mqtt.Client()
            client.connect(BROKER, PORT, 60)

            message = json.dumps({"command": "toggle"})
            topic = "smarthome/actuator/button"

            client.publish(topic, message)
            client.disconnect()

            print(f"📤 GUI Sent: {message} to {topic}")

            def on_message(client, userdata, msg):
                print(f"📥 DEBUG (GUI): Received - {msg.topic}: {msg.payload.decode()}")

            test_client = mqtt.Client()
            test_client.on_message = on_message
            test_client.connect(BROKER, PORT, 60)
            test_client.subscribe(topic)
            test_client.loop_start()

        except Exception as e:
            print(f"❌ Error sending MQTT command: {e}")

    def on_mqtt_message(self, client, userdata, msg):
        """Update the GUI with the latest relay status."""
        status = msg.payload.decode()
        print(f"📥 GUI Received Relay Status: {status}")  # Debugging
        self.relay_state = status  # שמירת מצב ה-Relay
        self.text_display.append(f"🔄 Relay is now: {status}")

    def send_custom_temperature(self):
        """Send a manually entered temperature value via MQTT."""
        temp_value = self.temp_input.text().strip()
        try:
            temp_float = float(temp_value)
            publish.single(CONTROL_TOPIC, f"temp:{temp_float}", hostname=BROKER)
            self.text_display.append(f"✅ Sent Custom Temperature: {temp_float}°C")
        except ValueError:
            self.text_display.append("❌ Invalid temperature format! Enter a valid number.")

    def load_data(self):
        """Load and display the latest sensor data, including alerts for high/low temperatures."""
        rows = self.get_latest_data()
        display_text = ""

        for row in rows:
            entry = f"[{row[0]}] {row[1]}: {row[2]}"
            
            # בדיקת האם ההודעה היא JSON תקין לפני ניסיון לפענח
            if row[2].startswith("{") and row[2].endswith("}"):
                try:
                    data = json.loads(row[2])
                    if "temperature" in data:
                        temp = data["temperature"]
                        if temp > 30:
                            entry += f"  ⚠️ WARNING: High Temperature {temp}°C 🔥"
                        elif temp < 20:
                            entry += f"  ⚠️ ALERT: Low Temperature {temp}°C ❄️"
                except Exception as e:
                    entry += f"  ❌ Error processing alert: {e}"

            display_text += entry + "\n"

        self.text_display.setText(display_text if display_text else "No data available")


    def get_latest_data(self, limit=20):
        """Retrieve the latest sensor data from the database."""
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, topic, message FROM sensor_data ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print(f"Error retrieving data: {e}")
            return []
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SmartHomeGUI()
    window.show()
    sys.exit(app.exec_())
