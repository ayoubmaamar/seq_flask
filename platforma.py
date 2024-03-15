# import base64
# import sys
# import time
# import hashlib
# import hmac
# import paho.mqtt.client as mqtt
# from cryptography.hazmat.primitives.asymmetric import dh
# from cryptography.hazmat.primitives.serialization import Encoding
# from cryptography.hazmat.primitives.serialization import ParameterFormat
# from cryptography.hazmat.primitives.serialization import PublicFormat
# from cryptography.hazmat.primitives.serialization import load_pem_public_key
# from something import decrypt
# import json
#
# # BYTE_SEPARATOR = b'\xff'
# BYTE_SEPARATOR = b'\\|'
# PASSWORD = '1234'
#
# active_devices = {}
#
# mqtt_client_name = "platform"
# mqtt_hostname = "oasishunter254.cloud.shiftr.io"
# mqtt_port = 1883
# mqtt_user = "oasishunter254"
#
# # The callback for when the client receives a CONNACK response from the server.
# def on_connect(client, userdata, flags, rc, dummy):
#     if rc == 0:
#         print("connected OK Returned code=", rc)
#     else:
#         print("Bad connection Returned code=", rc)
#
#     # Subscribing in on_connect() means that if we lose the connection and
#     # reconnect then subscriptions will be renewed.
#     client.subscribe("hola")
#     client.subscribe("handshake_response")
#     client.subscribe('temperature-data')
#
# # The callback for when a PUBLISH message is received from the server.
# def on_message(client, userdata, msg):
#     # print(userdata)
#     if msg.topic == "handshake_response":
#         # print(msg.payload.split(BYTE_SEPARATOR)[0].decode('utf-8'))
#         handshake_close(msg.payload)
#     elif msg.topic == "temperature-data":
#         iv, tag, ciphertext, publisher_id, timestamp = msg.payload.split(BYTE_SEPARATOR)
#         publisher_name_string = str(publisher_id, "utf-8")
#         timestamp_string = str(timestamp, "utf-8")
#         plaintext = int(decrypt(iv=iv, ciphertext=ciphertext, tag=tag, key=active_devices[publisher_name_string]))
#         print(f"Data from publisher ({publisher_name_string}): {plaintext} (timestamp: {timestamp_string})")
#
# def generate_id():
#     if len(active_devices) == 0:
#         return 1
#     else:
#         return 2
#
#
# def handshake_init():
#     parameters = dh.generate_parameters(generator=2, key_size=512)
#     global a_private_key
#     a_private_key = parameters.generate_private_key()
#     a_public_key = a_private_key.public_key()
#     params_pem = parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)
#     a_public_key_pem = a_public_key.public_bytes(Encoding.PEM,
#                                              PublicFormat.SubjectPublicKeyInfo)
#     key = '0123'
#     # Generate the hash.
#     password_bytes = bytes(key, 'utf-8')
#     sign = hmac.new(
#         password_bytes,
#         a_public_key_pem,
#         hashlib.sha256
#     ).hexdigest()
#     signature = bytes(sign, "utf-8")
#     # hand = params_pem + BYTE_SEPARATOR + a_public_key_pem + BYTE_SEPARATOR + signature
#     publisher_id = bytes(str(generate_id()), "utf-8")
#     data = {
#         "params_pem": params_pem,
#         "a_public_key": a_public_key,
#         "signature": signature,
#         "id": publisher_id
#     }
#     return data
#
#
# def handshake_close(msg):
#     payload_str = msg.payload.decode("utf-8")
#     # Parse the JSON string into a dictionary
#     data = json.loads(payload_str)
#
#     publisher_id = data["id"]
#     b_pk = load_pem_public_key(data["a_public_key"])
#     if (not isinstance(b_pk, dh.DHPublicKey)):
#         sys.exit('Protocol error: Alice received a wrong message!')
#     # global a_shared_key
#     a_shared_key = a_private_key.exchange(b_pk)
#     active_devices[publisher_id] = a_shared_key[:16]
#     # print("\nKey calculated by Alice = %s\n" % a_shared_key.hex())
#     print('HANDSHAKE DONE')
#
#
# client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_client_name)
# client.on_connect = on_connect
# client.on_message = on_message
#
# client.username_pw_set(mqtt_user, PASSWORD)
# client.connect(mqtt_hostname, mqtt_port, 60)
# client.loop_start()
#
#
# counter = -1
# while 1:
#     counter = counter + 1
#     if(counter % 5 == 0):
#         counter = 0
#         print('HANDSHAKE INITIATED')
#         hand = handshake_init()
#         client.publish("handshake", hand)
#
#     time.sleep(1)
import queue
import sys
import time
import hashlib
import hmac
import paho.mqtt.client as mqtt
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import ParameterFormat
from cryptography.hazmat.primitives.serialization import PublicFormat
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from something import decrypt
import uuid

# BYTE_SEPARATOR = b'\xff'
BYTE_SEPARATOR = b'\\|'
PASSWORD = '1234'

active_devices = {}

mqtt_client_name = "platform"
mqtt_hostname = "oasishunter254.cloud.shiftr.io"
mqtt_port = 1883
mqtt_user = "oasishunter254"

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc, dummy):
    if rc == 0:
        print("connected OK Returned code=", rc)
    else:
        print("Bad connection Returned code=", rc)

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("hola")
    client.subscribe("handshake_response")
    client.subscribe('temperature-data')
    client.subscribe('weather-data')
    client.subscribe('pressure-data')

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    # print(userdata)
    if msg.topic == "handshake_response":
        print(msg.payload.split(BYTE_SEPARATOR)[0].decode('utf-8'))
        handshake_close(msg.payload)
    elif msg.topic == "temperature-data" or msg.topic == "weather-data" or msg.topic == "pressure-data":
        # message_queue.put((msg.topic, msg.payload))
        iv, tag, ciphertext, publisher_name, publisher_id, timestamp = msg.payload.split(BYTE_SEPARATOR)
        publisher_name_string = str(publisher_name, "utf-8")
        timestamp_string = str(timestamp, "utf-8")
        # plaintext = int(decrypt(iv=iv, ciphertext=ciphertext, tag=tag, key=active_devices[publisher_name_string]))
        plaintext = decrypt(iv=iv, ciphertext=ciphertext, tag=tag, key=active_devices[publisher_name_string]).decode('utf-8')
        print(f"Data from publisher ({publisher_name_string}): {plaintext} (timestamp: {timestamp_string})")

def handshake_init():
    parameters = dh.generate_parameters(generator=2, key_size=512)
    global a_private_key
    a_private_key = parameters.generate_private_key()
    a_public_key = a_private_key.public_key()
    params_pem = parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)
    a_public_key_pem = a_public_key.public_bytes(Encoding.PEM,
                                             PublicFormat.SubjectPublicKeyInfo)
    key = '0123'
    # Generate the hash.
    password_bytes = bytes(key, 'utf-8')
    sign = hmac.new(
        password_bytes,
        a_public_key_pem,
        hashlib.sha256
    ).hexdigest()
    signature = bytes(sign, "utf-8")
    unique_id = uuid.uuid4()
    hand = params_pem + BYTE_SEPARATOR + a_public_key_pem + BYTE_SEPARATOR + signature + BYTE_SEPARATOR + unique_id.bytes
    return hand

def handshake_close(msg):
    separated_data = msg.split(BYTE_SEPARATOR)
    publisher_name = str(separated_data[0], "utf-8")
    b_pk = load_pem_public_key(separated_data[1])
    uuid = separated_data[2]
    if (not isinstance(b_pk, dh.DHPublicKey)):
        sys.exit('Protocol error: Alice received a wrong message!')
    # global a_shared_key
    a_shared_key = a_private_key.exchange(b_pk)
    active_devices[publisher_name] = a_shared_key[:16]
    print("\nKey calculated by Alice = %s\n" % a_shared_key.hex())
    print('HANDSHAKE DONE')

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_client_name)
client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set(mqtt_user, PASSWORD)
client.connect(mqtt_hostname, mqtt_port, 60)
client.loop_start()

counter = -1
while 1:

    counter = counter + 1
    if(counter % 5 == 0):
        counter = 0
        hand = handshake_init()
        print('HANDSHAKE INITIATED')
        client.publish("handshake", hand)

    time.sleep(1)