/**
 * 
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
 */

// This example depends on MQTT.js, visit https://github.com/mqttjs/MQTT.js to find out more
import mqtt from 'mqtt';
import fetch from 'node-fetch';

const PROTOCOLS = {
  MQTT_WSS: 'mqtt-wss',
  MQTTS: 'mqtts',
};

// endpoint to request credentials
const netfieldApiInfoEndpoint = 'APIURL/v1/keys/dataservice/info';
// endpoint to request devices info
const netfieldApiDevicesEndpoint = 'APIURL/v1/keys/dataservice/devices';
// api key to use
const netfieldApiKey = 'APIKEY';
// id of device to subscribe to
const deviceIdToSubscribeTo = 'DEVICEID';
// topic to subscribe to
const deviceSubscriptionTopic = '#';
// topic to publish to
const devicePublishTopic = 'test';
// message to publish to device
const devicePublishMessage = 'Hello World!';
// what protocol would you like to use, MQTT_WSS or MQTTS
const mqttProtocol = PROTOCOLS.MQTT_WSS;

async function startAsync() {
  // request credentials
  const infoResponse = await fetch(netfieldApiInfoEndpoint, {
    method: 'GET',
    headers: {
      accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: netfieldApiKey,
    },
  });
  const info = await infoResponse.json();
  if (infoResponse.status == 401) {
    throw new Error(`Failed to connect to api endpoint: ApiKey not authorized. Response: \n${JSON.stringify(info)}\n`);
  }
  if (infoResponse.status == 404) {
    throw new Error(`Failed to connect to api endpoint: API not found. Response: \n${JSON.stringify(info)}\n`);
  }
  if (infoResponse.status != 200) {
    throw new Error(`Failed to connect to api endpoint. Response: \n${JSON.stringify(info)}\n`);
  }
  console.log(`Connected to api endpoint successfully, fetched response:\n${JSON.stringify(info)}\n`);

  // request devices info
  const deviceResponse = await fetch(netfieldApiDevicesEndpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      accept: 'application/json',
      authorization: netfieldApiKey,
    },
    body: JSON.stringify({
      deviceIds: [deviceIdToSubscribeTo],
    }),
  });
  const deviceInfo = await deviceResponse.json();
  const { devices } = deviceInfo;
  devices.forEach((d) => console.log(`Device "${d.name}" with id ${d.deviceId} available.`));

  // build device mqtt topic to subscribe to
  const device = devices.find((c) => c.deviceId === deviceIdToSubscribeTo);
  if (device == null) {
    throw new Error(`Requested device with id ${deviceIdToSubscribeTo} not available.`);
  }
  const deviceBaseTopic = device.baseTopic;
  if (deviceBaseTopic == null) {
    throw new Error(`No device found or no access to device with id ${deviceIdToSubscribeTo}`);
  }
  const topic = deviceBaseTopic + deviceSubscriptionTopic;
  console.log('info', info);

  // connect to broker
  // to find out more about MQTT.js, visit https://github.com/mqttjs/MQTT.js
  const { endpoint } = info.endpoints.find((e) => e.protocol === mqttProtocol);
  console.log(`Connecting to ${endpoint}...`);
  const client = mqtt.connect(endpoint, {
    username: info.username,
    password: info.password,
  });

  client.on('error', (err) => {
    console.log(`Error: ${err}`);
  });

  // create handler for  events
  client.on('connect', () => {
    console.log('connected');
  });

  client.on('message', (payload, topic) => {
    console.log(`Received message:\nTopic:\n${topic}\nPayload:\n${payload}\n`);
  });

  // subscribe to topic
  client.subscribe(topic, {}, (err, granted) => {
    if (err) {
      console.log(`Subscription error: ${err}`);
    } else {
      granted.forEach(({ topic, qos }) =>
        console.log(`Subscribed to device with ID "${device.deviceId}" and topic ${topic} with Quality of Service ${qos}`),
      );
    }
  });

  // publish to topic
  const toDeviceTopic = `todevice/${deviceBaseTopic}${devicePublishTopic}`;
  client.publish(toDeviceTopic, devicePublishMessage, {}, (err) => {
    if (err) {
      console.log(`Publish error: ${err}`);
    } else {
      console.log(`Published the message "${devicePublishMessage}" to topic ${toDeviceTopic}`);
    }
  });

  // Wait 1h before closing connection
  await new Promise((r) => setTimeout(r, 1000 * 60 * 60));

  client.end();
}

startAsync();
