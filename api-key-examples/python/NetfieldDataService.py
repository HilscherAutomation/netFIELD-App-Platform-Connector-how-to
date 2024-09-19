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

from paho.mqtt import client as mqttClient
from urllib.parse import urlparse
import json
import os
import asyncio
import requests
import logging as log
import time

PROTOCOL = {"MQTT_WSS": "mqtt-wss", "MQTTS": "mqtts"}

netfieldApiInfoEndpoint = "APIURL/v1/keys/dataservice/info"
netfieldApiDevicesEndpoint = "APIURL/v1/keys/dataservice/devices"
netfieldApiKey = "APIKEY"
deviceIdToSubscribeTo = "DEVICEID"
deviceSubscriptionTopic = "#"
devicePublishTopic = "test"
devicePublishMessage = "Hello from python"
mqttProtocol = PROTOCOL["MQTT_WSS"]


async def main():
    # Configure logging
    DEFAULT_LOG_LEVEL = "INFO"
    LOG_LEVEL = os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    log.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s\n", level=LOG_LEVEL)

    # request credentials
    infoResponse = requests.get(
        netfieldApiInfoEndpoint,
        data={},
        headers={"accept": "application/json", "authorization": netfieldApiKey},
    )
    info = infoResponse.json()

    if infoResponse.status_code == 401:
        raise ValueError(
            "Failed to connect to api endpoint. ApiKey not authorized. Response : {}".format(
                info
            )
        )
    if infoResponse.status_code == 404:
        raise ValueError(
            "Failed to connect to api endpoint. API not found. Response : {}".format(
                info
            )
        )
    if infoResponse.status_code != 200:
        raise ValueError("Failed to connect to api endpoint. Response: {}".format(info))

    # request devices info
    deviceResponse = requests.post(
        netfieldApiDevicesEndpoint,
        headers={
            "Content-Type": "application/json",
            "accept": "application/json",
            "authorization": netfieldApiKey,
        },
        data=json.dumps({"deviceIds": [deviceIdToSubscribeTo]}),
    )
    devicesInfo = deviceResponse.json()

    for device in devicesInfo["devices"]:
        if "name" in device:
            name = device["name"]
        else:
            name = ""
        log.info(
            'Device "%s" with id %s available.', str(name), str(device["deviceId"])
        )

    # select the right device and build mqtt topic to subscribe to
    for device in devicesInfo["devices"]:
        for deviceid in device.values():
            if deviceid == deviceIdToSubscribeTo:
                deviceToSubscribe = device

    if deviceToSubscribe is None:
        raise ValueError(
            "Requested device with id %s not available.", deviceIdToSubscribeTo
        )
    deviceBaseTopic = deviceToSubscribe["baseTopic"]
    if deviceBaseTopic is None:
        raise ValueError(
            "No device found or no access to device with id %s", deviceIdToSubscribeTo
        )
    topic = deviceBaseTopic + deviceSubscriptionTopic

    # The callback for connection, diconnection, message and subscriptions
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.connected_flag = True
            log.info("Connected to mqtt broker: ")
            # subscribe to topic after connection
            mqttc.subscribe(topic)
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
            "Received message \n"
            + str(message.payload)
            + " on topic '"
            + message.topic
            + "' with QoS "
            + str(message.qos)
        )

    def on_subscribe(mqttc, obj, mid, qos):
        log.info(
            "Subscribed to device with ID "
            + str(deviceIdToSubscribeTo)
            + " and topic '"
            + str(topic)
            + "' with Quality of Service: "
            + str(qos)
        )

    # get the endpoint depending on used protocol
    # and parse its url to get the endpoint host and port
    host = ""
    port = 0
    for endpoint in info["endpoints"]:
        if endpoint["protocol"] == mqttProtocol:
            # parse url to get host and port
            parsed_url = urlparse(endpoint["endpoint"])
            host = parsed_url.hostname
            port = parsed_url.port
    log.info("# host is: %s \n", host)

    # connect to broker and subscribe
    transportProtocol = "websockets" if mqttProtocol == PROTOCOL["MQTT_WSS"] else "tcp"
    mqttc = mqttClient.Client(transport=transportProtocol, clean_session=True)
    mqttc.username_pw_set(info["username"], info["password"])
    mqttc.ws_set_options(path="/", headers=None)
    mqttc.tls_set()

    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_subscribe = on_subscribe

    mqttc.connect(host, port, 60)

    result = mqttc.publish(devicePublishTopic, devicePublishMessage)
    status = result[0]
    if status == 0:
        print(
            f"Published the message `{devicePublishMessage}` to topic `{devicePublishTopic}`"
        )
    else:
        print(f"Failed to send message to topic {devicePublishTopic}")
    mqttc.loop_start()

    # Time until disconnection
    time.sleep(30)
    mqttc.loop_stop()


if __name__ == "__main__":
    asyncio.run(main())
