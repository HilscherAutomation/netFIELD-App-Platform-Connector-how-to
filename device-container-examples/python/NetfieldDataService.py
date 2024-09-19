"""
MIT License
Copyright (c) 2024 Hilscher Gesellschaft fuer Systemautomation mbH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import paho.mqtt.client as mqttClient
import os
import asyncio
import logging as log
import time

PROTOCOL = {"MQTT_WSS": "mqtt-wss", "MQTTS": "mqtts"}

brokerUrl = "localhost"
port = 8883
subscriptionTopic = "#"
publishTopic = "test"
publishMessage = "Hello from python"
mqttProtocol = PROTOCOL["MQTT_WSS"]


async def main():
    # Configure logging
    DEFAULT_LOG_LEVEL = "INFO"
    LOG_LEVEL = os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    log.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s\n", level=LOG_LEVEL)

    # The callback for connection, diconnection, message and subscriptions
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.connected_flag = True
            log.info("Connected to mqtt broker: ")
            # subscribe to topic after connection
            mqttc.subscribe(subscriptionTopic)
        else:
            errors = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier  ",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorised",
            }
            error = errors.get(rc, "Unknown Error")
            log.warning("Cannot connect to mqtt broker: %s ", error)

    def on_message(client, userdata, message, tmp=None):
        log.info(
            " Received message \n"
            + str(message.payload)
            + " on topic '"
            + message.topic
            + "' with QoS "
            + str(message.qos)
        )

    def on_subscribe(mqttc, obj, mid, qos):
        log.info(
            "Subscribed to topic '"
            + str(subscriptionTopic)
            + "' with Quality of Service: "
            + str(qos)
        )

    # connect to broker and subscribe
    transportProtocol = "websockets" if mqttProtocol == PROTOCOL["MQTT_WSS"] else "tcp"
    mqttc = mqttClient.Client(transport=transportProtocol, clean_session=True)
    # if your broker requires authentication, uncomment below lines
    # mqttc.username_pw_set("your_username", "your_password")
    mqttc.ws_set_options(path="/", headers=None)
    mqttc.tls_set()

    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_subscribe = on_subscribe

    mqttc.connect(brokerUrl, port, 60)

    result = mqttc.publish(publishTopic, publishMessage)
    status = result[0]
    if status == 0:
        print(f"Published the message `{publishMessage}` to topic `{publishTopic}`")
    else:
        print(f"Failed to send message to topic {publishTopic}")
    mqttc.loop_start()

    # Time until disconnection
    time.sleep(30)
    mqttc.loop_stop()


if __name__ == "__main__":
    asyncio.run(main())
