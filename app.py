# app.py

from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import paho.mqtt.client as mqtt
import json
import datetime

try:
    from main import client  # Import the MQTT client from main.py
except Exception as e:
    print("Error importing client from main:", e)

app = Flask(__name__)
app.secret_key = '1234'

# MQTT client setup
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set("public", "public")  # Use actual MQTT credentials
client.connect("oasishunter254.cloud.shiftr.io", 1883, 60)

# MongoDB connection setup
mongo_client = MongoClient('mongodb+srv://seq_user:lkwnbnZBc5EH0You@cluster0.fj9cwqh.mongodb.net/?retryWrites=true&w=majority')
db = mongo_client["SEQ_DB"]
messages_collection = db["messages_collection"]
devices_collection = db["Devices_Collection"]

# @app.route('/messages/<topic>')
# def show_messages(topic):
#     # Fetch messages for the selected topic from MongoDB
#     messages = list(messages_collection.find({'topic': topic}, {'_id': 0}))
#     return render_template('messages.html', messages=messages, topic=topic)

# @app.route('/topics', methods=['GET', 'POST'])
# def select_topics():
#     if request.method == 'POST':
#         selected_topic = request.form['topic']
#         session['selected_topic'] = selected_topic
#         # Redirect to the messages page for the selected topic
#         return redirect(url_for('show_messages', topic=selected_topic))
    
#     # List of predefined topics
#     topics = ["hola", "handshake_response", "temperature-data", "weather-data", "pressure-data", "an"]
#     return render_template('select_topics.html', topics=topics)

@app.route('/messages')
def show_messages():
    # Fetch all messages from MongoDB
    messages = list(messages_collection.find({}, {'_id': 0}))
    return render_template('messages.html', messages=messages)

@app.route('/topics', methods=['GET', 'POST'])
def select_topics():
    if request.method == 'POST':
        # Redirect to the messages page
        return redirect(url_for('show_messages'))
    
    # List of predefined topics (not needed for showing all messages but kept if needed for other functionalities)
    topics = ["hola", "handshake_response", "temperature-data", "weather-data", "pressure-data", "an"]
    return render_template('select_topics.html', topics=topics)

@app.route('/register', methods=['GET', 'POST'])
def register_device():
    if request.method == 'POST':
        device_data = request.form.to_dict()
        device_data['status'] = "active"
        device_data['public_key'] = ("-----BEGIN PUBLIC KEY-----\n"
                                     "MIGbMFMGCSqGSIb3DQEDATBGAkEA4+uwryYkqdE0ckVLeCuXN657BflXVPUzcGLV\n"
                                     "xxcgl2TB+8c42nywQUzVZZxIOFBnMsEXm4JREtiTI8Cj9qe2zwIBAgNEAAJBANvn\n"
                                     "KtC/sr5pERL7pougEmu3xPKkFzyZSf/t17GgfSYwMA710/YirgW4e0iz1gm6Lvch\n"
                                     "e7F7+yPZO7ob2XjLMkc=\n"
                                     "-----END PUBLIC KEY-----")
        device_data['shared_key'] = "c33e80258d333310d9679b29165cbf6251ea4c4eb22199a191dd1dee27c27d5db7b32a2d443f599271059a05e6ee7554821299fdca6d1b3846a8ddcf59c7176e"

        if devices_collection.find_one({"device_id": device_data.get('device_id')}):
            return jsonify({'message': 'Device already registered'}), 409

        devices_collection.insert_one(device_data)
        return redirect(url_for('list_devices'))

    return render_template('register.html')

@app.route('/devices')
def list_devices():
    devices = list(devices_collection.find({}))
    return render_template('list_devices.html', devices=devices)

@app.route('/delete/<device_id>', methods=['POST'])
def delete_device(device_id):
    devices_collection.delete_one({'_id': ObjectId(device_id)})
    return redirect(url_for('list_devices'))

@app.route('/update/<device_id>', methods=['GET', 'POST'])
def update_device(device_id):
    device = devices_collection.find_one({'_id': ObjectId(device_id)})
    
    if request.method == 'POST':
        # Ensure all fields are available in the form
        updated_data = {
            "device_id": request.form.get('device_id', device['device_id']),
            "status": request.form.get('status', device['status']),
            "public_key": request.form.get('public_key', device['public_key']),
            "shared_key": request.form.get('shared_key', device['shared_key']),
        }
        devices_collection.update_one({'_id': ObjectId(device_id)}, {'$set': updated_data})
        return redirect(url_for('list_devices'))
    
    return render_template('update_device.html', device=device)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)