import paho.mqtt.client as mqtt
import hmac
import hashlib
import sys
import os
import time
import datetime
import paho.mqtt.publish as publish
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.asymmetric.dh import DHParameterNumbers
from cryptography.hazmat.primitives.serialization import PublicFormat
from cryptography.hazmat.primitives.serialization import load_pem_parameters
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import random
from something import encrypt

# BYTE_SEPARATOR = b'\xff'
BYTE_SEPARATOR = b'\\|'
PASSWORD = '1234'


mqtt_client_name = "Martin"
mqtt_hostname = "oasishunter254.cloud.shiftr.io"
mqtt_port = 1883
mqtt_user = "oasishunter254"
b_shared_key = ''

iv = os.urandom(16)
mode_CBC = modes.CBC(iv)


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc, dummy):
    if rc == 0:
        client.connected_flag = True  # Set connected flag to True upon successful connection
        print("connected OK Returned code=", rc)
    else:
        print("Bad connection Returned code=", rc)

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
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
    # Generate the hash.
    password_bytes = bytes(key, 'utf-8')
    sign = hmac.new(
        password_bytes,
        separated_data[1],
        hashlib.sha256
    ).hexdigest()
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

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    if(msg.topic == "handshake"):
        handshake_response = handshake(msg.payload)
        client.publish("handshake_response", handshake_response, qos=1)
    


client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_client_name)
client.on_connect = on_connect
client.on_message = on_message

# Loop until the connection to the MQTT broker is established
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

# print("Generando parámetros públicos...\n")
parameters = dh.generate_parameters(generator=2, key_size=512)
params_pem = parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)
# print("Parámetros públicos en formato PKCS3: ")
print(params_pem.decode("utf-8"))
# print("Parámetros públicos en formato numérico: ")

# print(premenna)
client.loop_start()

while 1:
    # Publish a message every second
    if b_shared_key != '':
        # Ensure the key is 16 bytes for AES-128, 24 bytes for AES-192, or 32 bytes for AES-256
        # If the key is shorter than required, you might need to hash it or use a key derivation function
        # For simplicity, we'll use the first 16 bytes here
        key = b_shared_key[:16]
        print(key)
        temp = random.randint(-30, 40)
        print(f"Temperature: {temp}")
        temp = bytes(str(temp), 'utf-8')
        timestamp = bytes(str(datetime.datetime.now()), "utf-8")
        iv, cipthertext, tag = encrypt(temp, key)
        byte_data = iv + BYTE_SEPARATOR + tag + BYTE_SEPARATOR + cipthertext + BYTE_SEPARATOR + bytes(mqtt_client_name, "utf-8") + BYTE_SEPARATOR + timestamp
        print(byte_data, end="\n\n")
        client.publish('temperature-data',byte_data)
    time.sleep(2)