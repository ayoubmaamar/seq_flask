from flask import Flask, request, render_template, redirect, url_for, session
import paho.mqtt.client as mqtt

app = Flask(__name__)
app.secret_key = '1234'

# MQTT client setup
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set("public", "public")

# Connect to MQTT broker
client.connect("brickgrabber135.cloud.shiftr.io", 1883, 60)
client.loop_start()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        topic = request.form['topic']
        session['selected_topic'] = topic  # Store selected topic in session
        # You can add logic here to subscribe or publish to the topic
        client.subscribe(topic)  # Example: subscribing to the selected topic
        return redirect(url_for('index'))
    return render_template('index.html')

@app.route('/publish', methods=['GET', 'POST'])
def publish():
    if request.method == 'POST' and 'selected_topic' in session:
        message = request.form['message']
        client.publish(session['selected_topic'], message)  # Publish message to selected topic
        return redirect(url_for('publish'))
    return render_template('publish.html')  # A simple form to enter a message for publishing

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

def on_message(client, userdata, msg):
    print(f"{msg.topic}: {msg.payload.decode('utf-8')}")

client.on_connect = on_connect
client.on_message = on_message

if __name__ == '__main__':
    app.run(debug=True)









# import paho.mqtt.client as mqtt
# import subscriber as ss
# import paho.mqtt.publish as publish

# import time


# mqtt_hostname = "brickgrabber135.cloud.shiftr.io"
# mqtt_port = 1883
# mqtt_user = "brickgrabber135"

# # The callback for when the client receives a CONNACK response from the server.
# def on_connect(client, userdata, flags, rc):
#     if rc == 0:
#         client.connected_flag = True  # set flag
#         print("connected OK Returned code=", rc)
#     else:
#         print("Bad connection Returned code=", rc)

#     # Subscribing in on_connect() means that if we lose the connection and
#     # reconnect then subscriptions will be renewed.
#     client.subscribe("hola")

# # The callback for when a PUBLISH message is received from the server.
# def on_message(client, userdata, msg):
#     print(msg.topic+": "+msg.payload.decode('utf-8'))


# client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
# client.on_connect = on_connect
# client.on_message = on_message


# client.username_pw_set("public","public")

# # flag = False
# # while not flag:
# pwd = input("Type your password: ")
# client.username_pw_set(mqtt_user, pwd)
# client.connect(mqtt_hostname, mqtt_port, 60)


# client.loop_start()

#---------------------------------------------

# client.connect("brickgrabber135.cloud.shiftr.io", 1883, 60)
# client.subscribe("paho/test/topic")

# # Si quiero que este escuchando para siempre:
# # client.loop_forever()
# # http://www.steves-internet-guide.com/loop-python-mqtt-client/

# # Inicia una nueva hebra

# mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
# mqttc.on_connect = ss.on_connect
# mqttc.on_message = ss.on_message
# mqttc.on_subscribe = ss.on_subscribe
# mqttc.on_unsubscribe = ss.on_unsubscribe

# # Our application produce some messages
# msg_info = mqttc.publish("paho/test/topic", "my message", qos=1)
# unacked_publish.add(msg_info.mid)

# mqttc.user_data_set([])
# mqttc.connect("mqtt.eclipseprojects.io")
# mqttc.subscribe("paho/test/topic")

# client.loop_start()
# message = "It works!!"
# publish.single("paho/topic/test", message, hostname='localhost')

# while 1:
#     # Publish a message every second
#     publish.single("paho/topic/test", message, hostname='localhost')
#     time.sleep(1)

# # También se puede conectar y enviar en una linea https://www.eclipse.org/paho/clients/python/docs/#single

# # Y conectar y bloquear para leer una sola vez en una sola linea https://www.eclipse.org/paho/clients/python/docs/#simple










