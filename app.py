from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from paho.mqtt import client as mqtt_client
from flask_socketio import SocketIO

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import json
import sys
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import PublicFormat
from cryptography.hazmat.primitives.asymmetric.dh import DHParameterNumbers
from cryptography.hazmat.primitives.serialization import load_pem_public_key

app = Flask(__name__)
socketio = SocketIO(app)

# MQTT client setup
mqtt_client_name = "Platform"
mqtt_hostname = "brickgrabber135.cloud.shiftr.io"
mqtt_port = 1883
mqtt_user = "brickgrabber135"

mqtt_client = mqtt_client.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_client_name)
mqtt_client.username_pw_set(username=mqtt_user, password='1234')  # Add password if necessary

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected OK Returned code=", rc)
        client.subscribe("device/registration")
    else:
        print("Bad connection Returned code=", rc)

def on_message(client, userdata, msg):
    if msg.topic == "device/registration":
        # Extract device information from the message
        # Assuming the message payload is 'device_id,device_name'
        device_info = msg.payload.decode().split(',')
        device_id = device_info[0]
        device_name = device_info[1] if len(device_info) > 1 else "Unknown"

        # Insert the new device into the MongoDB collection
        devices_collection.insert_one({'device_id': device_id, 'device_name': device_name})
        print(f"Registered new device: {device_id} - {device_name}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(mqtt_hostname, mqtt_port, 60)
mqtt_client.loop_start()

@socketio.on('connect')
def test_connect():
    print('Client connected')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')



# MongoDB Atlas setup
uri = "mongodb+srv://seq_user:lkwnbnZBc5EH0You@cluster0.fj9cwqh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(uri)
db = mongo_client['SEQ_DB']
devices_collection = db['devices_collection']

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        device_id = request.form['device_id']
        device_name = request.form['device_name']
        devices_collection.insert_one({'device_id': device_id, 'device_name': device_name})
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/devices', methods=['GET', 'POST'])
def manage_devices():
    if request.method == 'POST':
        device_id_to_remove = request.form.get('device_id')
        if device_id_to_remove:
            devices_collection.delete_one({'device_id': device_id_to_remove})
            return redirect(url_for('manage_devices'))
    devices = list(devices_collection.find())
    return render_template('devices.html', devices=devices)

@app.route('/topics', methods=['GET', 'POST'])
def select_topics():
    if request.method == 'POST':
        topic = request.form['topic']
        mqtt_client.subscribe(topic)
        print(f"Subscribed to {topic}")
        return redirect(url_for('home'))
    return render_template('topics.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)
