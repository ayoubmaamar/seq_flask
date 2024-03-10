import paho.mqtt.client as mqtt
import hmac
import hashlib
import sys
import os
import time
import datetime
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat, Encoding, PublicFormat, load_pem_parameters, load_pem_public_key
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from pymongo.mongo_client import MongoClient
import random
from something import encrypt

# MongoDB connection setup
uri = "mongodb+srv://seq_user:lkwnbnZBc5EH0You@cluster0.fj9cwqh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Replace this with your actual MongoDB URI
mongo_client = MongoClient(uri)
db = mongo_client["SEQ_DB"]
devices_collection = db["Devices_Collection"]

# BYTE_SEPARATOR = b'\xff'
BYTE_SEPARATOR = b'\\|'
PASSWORD = '1234'
mqtt_client_name = "Martin"
mqtt_hostname = "chainhare753.cloud.shiftr.io"
mqtt_port = 1883
mqtt_user = "chainhare753"
b_shared_key = ''
iv = os.urandom(16)

# Callback for when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rc, dummy):
    if rc == 0:
        client.connected_flag = True  # Set connected flag to True upon successful connection
        print("Connected OK Returned code=", rc)
    else:
        print("Bad connection Returned code=", rc)
    client.subscribe("hola")
    client.subscribe("handshake")
    client.subscribe('temperature-data')

# Handshake process
def handshake(msg):
    separated_data = msg.split(BYTE_SEPARATOR)
    dh_params = load_pem_parameters(separated_data[0])
    a_pk = load_pem_public_key(separated_data[1])
    if not isinstance(dh_params, dh.DHParameters) or not isinstance(a_pk, dh.DHPublicKey):
        sys.exit('Protocol error: Bob received a wrong message!')
    key = '0123'
    password_bytes = bytes(key, 'utf-8')
    sign = hmac.new(password_bytes, separated_data[1], hashlib.sha256).hexdigest()
    signature = bytes(sign, "utf-8")
    if signature != separated_data[2]:
        print("Wrong authentication")
        sys.exit('Authentication failed')
    b_private_key = dh_params.generate_private_key()
    b_public_key = b_private_key.public_key()
    global b_shared_key
    b_shared_key = b_private_key.exchange(a_pk)
    print("\nKey calculated by Bob = %s\n" % b_shared_key.hex())
    b_public_key_pem = b_public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

    # Update device info in MongoDB
    device_info = {
        "device_id": mqtt_client_name,
        "public_key": b_public_key_pem.decode("utf-8"),
        "shared_key": b_shared_key.hex(),
        "status": "active"
    }
    devices_collection.update_one({"device_id": mqtt_client_name}, {"$set": device_info}, upsert=True)

from bson import binary

def on_message(client, userdata, msg):
    if msg.topic == "handshake":
        handshake_response = handshake(msg.payload)
        client.publish("handshake_response", handshake_response, qos=1)
    elif msg.topic == "temperature-data":
        print("Received temperature data message.")
        iv, tag, ciphertext, publisher_id, timestamp = msg.payload.split(BYTE_SEPARATOR)
        publisher_name = publisher_id.decode('utf-8')
        if publisher_name in active_devices:
            decrypted_data = decrypt(iv, ciphertext, tag, active_devices[publisher_name])
            message_data = {
                "device_id": publisher_name,
                "timestamp": datetime.datetime.now(),
                "data": decrypted_data
            }
            print(f"Inserting data into Message_Data: {message_data}")
            result = db["Message_Data"].insert_one(message_data)
            print(f"Data insertion result: {result.inserted_id}")
        else:
            print(f"No shared key found for publisher {publisher_name}. Unable to decrypt message.")


client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_client_name)
client.on_connect = on_connect
client.on_message = on_message

# Loop until the connection to the MQTT broker is established
while True:
    pwd = input("Type your password: ")
    if pwd == PASSWORD:
        client.username_pw_set(mqtt_user, pwd)
        client.connect(mqtt_hostname, mqtt_port, 60)
        client.loop_start()
        break
    else:
        print("Incorrect password. Please try again")

parameters = dh.generate_parameters(generator=2, key_size=512)
params_pem = parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)
print(params_pem.decode("utf-8"))

client.loop_start()

while True:
    if b_shared_key != '':
        key = b_shared_key[:16]
        temp = random.randint(-30, 40)
        print(f"Temperature: {temp}")
        temp = bytes(str(temp), 'utf-8')
        timestamp = bytes(str(datetime.datetime.now()), "utf-8")
        iv, ciphertext, tag = encrypt(temp, key)
        byte_data = iv + BYTE_SEPARATOR + tag + BYTE_SEPARATOR + ciphertext + BYTE_SEPARATOR + bytes(mqtt_client_name, "utf-8") + BYTE_SEPARATOR + timestamp
        print(byte_data, end="\n\n")
        client.publish('temperature-data', byte_data)
    time.sleep(2)











