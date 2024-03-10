from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from paho.mqtt import client as mqtt_client
from flask_socketio import SocketIO
import threading
import json

app = Flask(__name__)
socketio = SocketIO(app)

# MongoDB connection setup
uri = "mongodb+srv://seq_user:lkwnbnZBc5EH0You@cluster0.fj9cwqh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Replace this with your actual MongoDB URI
mongo_client = MongoClient(uri)
db = mongo_client["SEQ_DB"]
devices_collection = db["Devices_Collection"]
topics_collection = db["Topics_Collection"]

# MQTT setup
mqtt_hostname = "chainhare753.cloud.shiftr.io"
mqtt_port = 1883
mqtt_user = "chainhare753"
mqtt_password = "1234"  # Replace with your MQTT broker's password

def listen_for_device_info():
    def on_connect(client, userdata, flags, rc):
        client.subscribe("device_info_topic")

    def on_message(client, userdata, message):
        data = json.loads(message.payload.decode())
        device_info = {
            "device_id": data['device_id'],
            "additional_info": data.get('additional_info', 'No additional info')
        }
        devices_collection.update_one({"device_id": device_info["device_id"]}, {"$set": device_info}, upsert=True)
        socketio.emit('device_update', device_info)

    client = mqtt_client.Client()
    client.username_pw_set(username=mqtt_user, password=mqtt_password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_broker, mqtt_port)
    client.loop_start()

# Start MQTT listener thread
thread = threading.Thread(target=listen_for_device_info)
thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/devices', methods=['GET', 'POST'])
def devices():
    if request.method == 'POST':
        device_id = request.form.get('device_id')
        devices_collection.insert_one({'device_id': device_id, 'status': 'active'})
        return redirect(url_for('devices'))
    else:
        devices = list(devices_collection.find())
        return render_template('devices.html', devices=devices)

@app.route('/remove_device/<device_id>')
def remove_device(device_id):
    devices_collection.delete_one({'device_id': device_id})
    return redirect(url_for('devices'))


@app.route('/messages')
def messages():
    current_time = datetime.now()
    messages = db["Message_Data"].find({}, {'_id': 0, 'device_id': 1, 'timestamp': 1, 'data': 1}).sort("timestamp", -1).limit(50)  # Fetch the latest 50 messages
    return render_template('messages.html', messages=messages)


from datetime import datetime, timedelta

@app.route('/topics', methods=['GET', 'POST'])
def topics():
    if request.method == 'POST':
        selected_topic = request.form.get('selected_topic')
        messages = None
        num_messages = int(request.form.get('num_messages', 10))  # Default to 10 messages if not specified
        if selected_topic == 'temperature-data':
            current_time = datetime.now()
            messages = db["Message_Data"].find({'timestamp': {'$gt': current_time - timedelta(hours=1)}}, {'_id': 0, 'device_id': 1, 'timestamp': 1, 'data': 1}).limit(num_messages)
        return render_template('topics.html', topics=list(topics_collection.find()), messages=messages, selected_topic=selected_topic, num_messages=num_messages)
    else:
        current_time = datetime.now()
        messages = db["Message_Data"].find({'timestamp': {'$gt': current_time - timedelta(hours=1)}}, {'_id': 0, 'device_id': 1, 'timestamp': 1, 'data': 1}).limit(10)
        return render_template('topics.html', topics=list(topics_collection.find()), messages=messages, selected_topic=None, num_messages=10)

if __name__ == '__main__':
    app.run(debug=True)










