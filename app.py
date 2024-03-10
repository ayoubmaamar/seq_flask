from flask import Flask, render_template, request, jsonify
import paho.mqtt.client as mqtt
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# Flask app initialization
app = Flask(__name__)

# MQTT settings
MQTT_BROKER_URL = "oasishunter254.cloud.shiftr.io"
MQTT_BROKER_PORT = 1883
MQTT_USERNAME = "oasishunter254"
MQTT_PASSWORD = "1234"  # Assuming this is the password you want to use for MQTT
MQTT_KEEPALIVE = 60
MQTT_TOPIC = "temperature-data"  # Define the topic you want to listen to

# Device registry
devices = {}

# MQTT client initialization
mqtt_client = mqtt.Client("Martin")

# Initialize encryption settings
BYTE_SEPARATOR = b'\\|'
iv = os.urandom(16)
mode_CBC = modes.CBC(iv)  # CBC mode initialization with the IV

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    print(f"Message received on topic {msg.topic}: {msg.payload.decode()}")
    # Device registration logic
    # Assuming the message payload contains device_id and other details separated by BYTE_SEPARATOR
    payload_data = msg.payload.split(BYTE_SEPARATOR)
    device_id = payload_data[0].decode()
    device_data = payload_data[1:]
    devices[device_id] = {'data': device_data}

# MQTT client configuration
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.connect(MQTT_BROKER_URL, MQTT_BROKER_PORT, MQTT_KEEPALIVE)

# Flask route example
@app.route('/')
def index():
    return render_template('index.html', devices=devices)

# Running the Flask app
if __name__ == '__main__':
    mqtt_client.loop_start()  # Start the MQTT client loop
    app.run(debug=True)  # Start the Flask application
