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

const brokerUrl = 'mqtt://localbroker:port';
const subscriptionTopic = '#';
const publishTopic = 'test';
const publishMessage = 'Hello World!';

async function startAsync() {
  // connect to broker
  const client = mqtt.connect(brokerUrl, {
    clean: true, // retain session
    connectTimeout: 30000, // Timeout period increased to 30 seconds
    // Authentication information
    clientId: `${Math.floor(Math.random() * 10000)}`,
    // if your broker requires authentication, use the following
    // username: 'username', // replace with your username
    // password: 'password', // replace with your password
  });
  // create handler for  events
  client.on('error', (error) => {
    console.log('Connection failed:', error);
  });

  client.on('connect', () => {
    console.log('connected');
  });

  client.on('message', (payload, topic) => {
    console.log(`Received message:\nTopic:\n${topic}\nPayload:\n${payload}\n`);
  });

  // subscribe to topic
  client.subscribe(subscriptionTopic, {}, (err, granted) => {
    if (err) {
      console.log(`Subscription error: ${err}`);
    } else {
      granted.forEach(({ topic, qos }) => console.log(`Subscribed to topic ${topic} with Quality of Service ${qos}`));
    }
  });

  // publish to topic
  client.publish(publishTopic, publishMessage, {}, (err) => {
    if (err) {
      console.log(`Publish error: ${err}`);
    } else {
      console.log(`Published the message "${publishMessage}" to topic ${publishTopic}`);
    }
  });

  // Wait 1h before closing connection
  await new Promise((r) => setTimeout(r, 1000 * 60 * 60));

  client.end();
}

startAsync();
