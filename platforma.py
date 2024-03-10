import sys
import time
import hashlib
import hmac
import paho.mqtt.client as mqtt
from pymongo.mongo_client import MongoClient
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import Encoding, ParameterFormat, PublicFormat, load_pem_public_key
from something import decrypt

# MongoDB connection setup
uri = "mongodb+srv://seq_user:lkwnbnZBc5EH0You@cluster0.fj9cwqh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Replace this with your actual MongoDB URI
mongo_client = MongoClient(uri)
db = mongo_client["SEQ_DB"]
devices_collection = db["Devices_Collection"]
topics_collection = db["Topics_Collection"]

# MQTT and Cryptography setup
BYTE_SEPARATOR = b'\\|'
PASSWORD = '1234'
active_devices = {}
mqtt_client_name = "platform"
mqtt_hostname = "chainhare753.cloud.shiftr.io"
mqtt_port = 1883
mqtt_user = "Chainhare753"

# Callback for when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rc, dummy):
    if rc == 0:
        print("Connected OK Returned code=", rc)
    else:
        print("Bad connection Returned code=", rc)
    client.subscribe("hola")
    client.subscribe("handshake_response")
    client.subscribe('temperature-data')

# Callback for when a PUBLISH message is received from the server
def on_message(client, userdata, msg):
    if msg.topic == "handshake_response":
        handshake_close(msg.payload)
    elif msg.topic == "temperature-data":
        process_temperature_data(msg.payload)

def handshake_init():
    parameters = dh.generate_parameters(generator=2, key_size=512)
    global a_private_key
    a_private_key = parameters.generate_private_key()
    a_public_key = a_private_key.public_key()
    params_pem = parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)
    a_public_key_pem = a_public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    key = '0123'
    password_bytes = bytes(key, 'utf-8')
    sign = hmac.new(password_bytes, a_public_key_pem, hashlib.sha256).hexdigest()
    signature = bytes(sign, "utf-8")
    hand = params_pem + BYTE_SEPARATOR + a_public_key_pem + BYTE_SEPARATOR + signature
    return hand

def handshake_close(msg):
    separated_data = msg.split(BYTE_SEPARATOR)
    publisher_name = str(separated_data[0], "utf-8")
    b_pk = load_pem_public_key(separated_data[1])
    if not isinstance(b_pk, dh.DHPublicKey):
        sys.exit('Protocol error: Alice received a wrong message!')
    a_shared_key = a_private_key.exchange(b_pk)
    active_devices[publisher_name] = a_shared_key[:16]
    print("\nKey calculated by Alice = %s\n" % a_shared_key.hex())

    # Update device info in MongoDB
    devices_collection.update_one(
        {"device_id": publisher_name},
        {"$set": {"shared_key": a_shared_key.hex(), "status": "active"}},
        upsert=True
    )

    # Update topic info in MongoDB
    topics_collection.update_one(
        {"topic_name": "handshake_response"},
        {"$set": {"related_device": publisher_name, "purpose": "Handshake response"}},
        upsert=True
    )

def process_temperature_data(payload):
    iv, tag, ciphertext, publisher_id, timestamp = payload.split(BYTE_SEPARATOR)
    publisher_name_string = str(publisher_id, "utf-8")
    if publisher_name_string in active_devices:
        plaintext = int(decrypt(iv=iv, ciphertext=ciphertext, tag=tag, key=active_devices[publisher_name_string]))
        print(f"Data from publisher ({publisher_name_string}): {plaintext} (timestamp: {timestamp.decode('utf-8')})")

        # Update topic info in MongoDB for temperature data
        topics_collection.update_one(
            {"topic_name": "temperature-data"},
            {"$set": {"related_device": publisher_name_string, "purpose": "Temperature data"}},
            upsert=True
        )

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

counter = -1
while True:
    counter += 1
    if counter % 5 == 0:
        counter = 0
        hand = handshake_init()
        print('HANDSHAKE DONE')
        client.publish("handshake", hand)
    time.sleep(1)
