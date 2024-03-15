import paho.mqtt.client as mqtt
import hmac
import hashlib
import sys
import os
import time
import datetime
import random
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat, Encoding, PublicFormat
from cryptography.hazmat.primitives.serialization import load_pem_parameters, load_pem_public_key
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from something import encrypt, decrypt  # Added decrypt import
from pymongo import MongoClient

BYTE_SEPARATOR = b'\\|'
PASSWORD = '1234'

mqtt_client_name = "Martin"
mqtt_hostname = "oasishunter254.cloud.shiftr.io"
mqtt_port = 1883
mqtt_user = "oasishunter254"
b_shared_key = ''

iv = os.urandom(16)

# MongoDB connection setup
mongo_client = MongoClient('mongodb+srv://seq_user:lkwnbnZBc5EH0You@cluster0.fj9cwqh.mongodb.net/?retryWrites=true&w=majority')
db = mongo_client["SEQ_DB"]
messages_collection = db["messages_collection"]
devices_collection = db["Devices_Collection"]

def on_connect(client, userdata, flags, rc, dummy):
    if rc == 0:
        client.connected_flag = True
        print("connected OK Returned code=", rc)
    else:
        print("Bad connection Returned code=", rc)
    client.subscribe("hola")
    client.subscribe("handshake")
    client.subscribe('temperature-data')

def handshake(msg):
    separated_data = msg.split(BYTE_SEPARATOR)
    dh_params = load_pem_parameters(separated_data[0])
    a_pk = load_pem_public_key(separated_data[1])
    if (not isinstance(dh_params, dh.DHParameters)
            or not isinstance(a_pk, dh.DHPublicKey)):
        sys.exit('Protocol error: Bob received a wrong message!')
    key = '0123'
    password_bytes = bytes(key, 'utf-8')
    sign = hmac.new(password_bytes, separated_data[1], hashlib.sha256).hexdigest()
    signature = bytes(sign, "utf-8")
    if(signature != separated_data[2]):
        print("Wrong authentication")
        sys.exit('Authentication failed')
    b_private_key = dh_params.generate_private_key()
    b_public_key = b_private_key.public_key()
    global b_shared_key
    b_shared_key = b_private_key.exchange(a_pk)
    print("\nKey calculated by Bob = %s\n" % b_shared_key.hex())
    b_public_key_pem = b_public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    device_id = bytes(mqtt_client_name, 'utf-8')
    return device_id + BYTE_SEPARATOR + b_public_key_pem

def on_message(client, userdata, msg):
    if(msg.topic == "handshake"):
        handshake_response = handshake(msg.payload)
        client.publish("handshake_response", handshake_response, qos=1)
    else:
        global b_shared_key
        if b_shared_key != '':
            key = b_shared_key[:16]
            temp = random.randint(-30, 40)
            print(f"Temperature: {temp}")
            temp_bytes = bytes(str(temp), 'utf-8')
            timestamp = datetime.datetime.now()
            iv, ciphertext, tag = encrypt(temp_bytes, key)
            # Decryption added here for demonstration
            decrypted_temp_bytes = decrypt(iv, ciphertext, tag, key)  # Assuming the decrypt function signature matches
            
            message_data = {
                "iv": iv,
                "tag": tag,
                "ciphertext": ciphertext,
                "decrypted_temp": decrypted_temp_bytes.decode('utf-8'),  # Storing decrypted data
                "client_name": mqtt_client_name,
                "timestamp": timestamp,
                "topic": msg.topic,
            }
            try:
                messages_collection.insert_one(message_data)
            except Exception as e:
                print(f"Error inserting message into MongoDB: {e}")

            byte_data = iv + BYTE_SEPARATOR + tag + BYTE_SEPARATOR + ciphertext + BYTE_SEPARATOR + bytes(mqtt_client_name, "utf-8") + BYTE_SEPARATOR + bytes(str(timestamp), "utf-8")
            client.publish('temperature-data', byte_data)

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_client_name)
client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set(mqtt_user, PASSWORD)
client.connect(mqtt_hostname, mqtt_port, 60)
client.loop_start()

parameters = dh.generate_parameters(generator=2, key_size=512)
params_pem = parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)
print(params_pem.decode("utf-8"))

client.loop_start()

while True:
    time.sleep(2)
