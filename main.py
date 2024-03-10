import paho.mqtt.client as mqtt
import sys
from pymongo.mongo_client import MongoClient

# MongoDB connection setup
uri = "your_mongodb_uri"  # Replace this with your actual MongoDB URI
mongo_client = MongoClient(uri)
db = mongo_client["SEQ_DB"]
devices_collection = db["Devices_Collection"]
topics_collection = db["Topics_Collection"]

mqtt_hostname = "oasishunter254.cloud.shiftr.io"
mqtt_port = 1883
mqtt_user = "oasishunter254"
PASSWORD = '1234'

# The callback for when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.connected_flag = True
        print("Connected OK Returned code=", rc)
    else:
        print("Bad connection Returned code=", rc)

    # Subscribe to topics based on the topics collection
    topics = topics_collection.find({})
    for topic in topics:
        client.subscribe(topic["topic_name"])

# The callback for when a PUBLISH message is received from the server
def on_message(client, userdata, msg):
    print(f"Message received on topic {msg.topic}: {msg.payload.decode('utf-8')}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
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

# Main loop to keep the client running
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Disconnecting from broker")
    client.disconnect()
    sys.exit()
