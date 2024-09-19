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
 
using MQTTnet;
using MQTTnet.Client;
using NetfieldDataServiceExample.Models;
using System.Text;
using System.Text.Json;

ConnectionOptions connectionOptions = new ConnectionOptions
{
  MQTTS = "mqtts",
  MQTT_WSS = "mqtt-wss"
};

string netfieldApiInfoEndpoint = "APIURL/v1/keys/dataservice/info";
string netfieldApiDevicesEndpoint = "APIURL/v1/keys/dataservice/devices";
string netfieldApiKey = "APIKEY";
string deviceIdToSubscribeTo = "DEVICEID";
string deviceSubscriptionTopic = "#";
string devicePublishTopic = "test";
string devicePublishMessage = "Hello World!";
string connectionProtocol = connectionOptions.MQTT_WSS;


/// <summary>
/// Publishes a message to a topic
/// </summary>
/// <param name="host">The host to connect to</param>
/// <param name="port">The port to connect to</param>
/// <param name="protocol">The protocol to use</param>
/// <param name="info">The info response from the api with username and password</param>
/// <param name="topic">The topic to publish to</param>
/// <param name="payload">The payload to publish</param>
/// <returns></returns>
async Task Publish_Application_Message(string host, int port, string protocol, InfoResponse info, string topic, string payload)
{
  var mqttFactory = new MqttFactory();

  // create mqtt client
  using var mqttClient = mqttFactory.CreateMqttClient();
  // create options depending on protocol
  var mqttClientOptionsBuilder = new MqttClientOptionsBuilder();
  // add websocket or tcp server depending on protocol
  mqttClientOptionsBuilder = protocol == connectionOptions.MQTT_WSS ? mqttClientOptionsBuilder.WithWebSocketServer($"{host}:{port}") : mqttClientOptionsBuilder.WithTcpServer(host, port);
  // build options
  var mqttClientOptions = mqttClientOptionsBuilder.WithClientId(Guid.NewGuid().ToString())
    .WithKeepAlivePeriod(TimeSpan.FromSeconds(10))
    .WithCredentials(info.Username, info.Password)
    .WithTimeout(TimeSpan.FromSeconds(5))
    .WithTls()
    .Build();

  // connect to mqtt broker
  await mqttClient.ConnectAsync(mqttClientOptions, CancellationToken.None);

  // create toDevice topic
  string toDeviceTopic = $"todevice/{topic}";
  // create publish configuration
  var applicationMessage = new MqttApplicationMessageBuilder()
      .WithTopic(toDeviceTopic)
      .WithPayload(payload)
      .WithRetainFlag()
      .Build();
  // publish message
  await mqttClient.PublishAsync(applicationMessage, CancellationToken.None);
  Console.WriteLine($"Published message \"{payload}\" to topic {topic}");

  // disconnect from mqtt broker
  await mqttClient.DisconnectAsync();
}


/// <summary>
/// Subscribes to a topic and waits for messages
/// </summary>
/// <param name="host">The host to connect to</param>
/// <param name="port">The port to connect to</param>
/// <param name="protocol">The protocol to use</param>
/// <param name="info">The info response from the api with username and password</param>
/// <param name="topic">The topic to subscribe to</param>
/// <returns></returns>
/// <remarks>
/// This method will wait for 1h before stopping the app.
/// </remarks>
async Task Subscribe_Topic(string host, int port, string protocol, InfoResponse info, string topic)
{
  var mqttFactory = new MqttFactory();

  // create mqtt client
  using var mqttClient = mqttFactory.CreateMqttClient();
  // create options depending on protocol
  var mqttClientOptionsBuilder = new MqttClientOptionsBuilder();
  // add websocket or tcp server depending on protocol
  mqttClientOptionsBuilder = protocol == connectionOptions.MQTT_WSS ? mqttClientOptionsBuilder.WithWebSocketServer($"{host}:{port}") : mqttClientOptionsBuilder.WithTcpServer(host, port);
  // build options
  var mqttClientOptions = mqttClientOptionsBuilder.WithClientId(Guid.NewGuid().ToString())
    .WithKeepAlivePeriod(TimeSpan.FromSeconds(10))
    .WithCredentials(info.Username, info.Password)
    .WithTimeout(TimeSpan.FromSeconds(5))
    .WithTls()
    .Build();

  // add event handler for received messages
  mqttClient.ApplicationMessageReceivedAsync += e =>
  {
    Console.WriteLine($"Received message:\n" +
                $"Topic:\n{e.ApplicationMessage.Topic}\n" +
                $"Payload:\n{e.ApplicationMessage.ConvertPayloadToString()}\n\n");
    return Task.CompletedTask;
  };

  // connect to mqtt broker
  await mqttClient.ConnectAsync(mqttClientOptions, CancellationToken.None);
  Console.WriteLine("connected");

  // create subscription options
  var mqttSubscribeOptions = mqttFactory.CreateSubscribeOptionsBuilder()
      .WithTopicFilter(
          f =>
          {
            f.WithTopic(topic);
          })
      .Build();

  // subscribe to topic
  var response = await mqttClient.SubscribeAsync(mqttSubscribeOptions, CancellationToken.None);
  Console.WriteLine($"Subscribed to topic {topic}");

  // Wait 1h before stopping app
  Thread.Sleep(TimeSpan.FromHours(1));

  // disconnect from mqtt broker
  await mqttClient.DisconnectAsync();
}


// create a https client to request api endpoint
var httpClientHandler = new HttpClientHandler();
httpClientHandler.ServerCertificateCustomValidationCallback = null;
var httpClient = new HttpClient(httpClientHandler);

//  request credentials info
HttpRequestMessage infoRequest = new HttpRequestMessage();
infoRequest.Method = HttpMethod.Get;
infoRequest.RequestUri = new Uri(netfieldApiInfoEndpoint);
infoRequest.Headers.Add("authorization", netfieldApiKey);

// make request
HttpResponseMessage infoResponse = await httpClient.SendAsync(infoRequest);
if (!infoResponse.IsSuccessStatusCode)
  throw new ArgumentNullException("Connection to api endpoint failed. Response: ", infoResponse.ToString());

// parse response
string infoContent = await infoResponse.Content.ReadAsStringAsync();
InfoResponse info = JsonSerializer.Deserialize<InfoResponse>(infoContent)!;
Console.WriteLine($"Fetched response from API:\n{infoContent}");

// request devices info
HttpRequestMessage devicesRequest = new HttpRequestMessage();
var devicesJsonPayload = JsonSerializer.Serialize(new DevicesRequest()
{
  DeviceIds = new() {
    deviceIdToSubscribeTo
  }
});
var payload = new StringContent(devicesJsonPayload, Encoding.UTF8, "application/json");
devicesRequest.Content = payload;
devicesRequest.Method = HttpMethod.Post;
devicesRequest.RequestUri = new Uri(netfieldApiDevicesEndpoint);
devicesRequest.Headers.Add("authorization", netfieldApiKey);

// make request
HttpResponseMessage response = await httpClient.SendAsync(devicesRequest);
if (!response.IsSuccessStatusCode)
  throw new ArgumentNullException("Connection to api endpoint failed. Response: ", response.ToString());

// parse response
string responseContent = await response.Content.ReadAsStringAsync();
DevicesResponse devicesResponse = JsonSerializer.Deserialize<DevicesResponse>(responseContent)!;
Console.WriteLine($"Fetched response from API:\n{responseContent.ToString()}");

// show available devices
var devices = devicesResponse.Devices;
devices.ForEach(d => Console.WriteLine($"Device \"{d.Name}\" with id {d.DeviceId} available."));

// create mqtt client
// to find out more about MQTTlib, visit https://github.com/dotnet/MQTTnet
var mqttFactory = new MqttFactory();
var mqttClient = mqttFactory.CreateMqttClient();

// find endpoint url according to protocol
string endpointUrl = info.Endpoints!.Find(e => e.Protocol == connectionProtocol)!.EndpointUrl;
var uri = new Uri(endpointUrl);
var host = uri.Host;
var port = uri.Port;

// find device base topic
var deviceBaseTopic = devicesResponse.Devices.Find(c => c.DeviceId == deviceIdToSubscribeTo)!.BaseTopic;
if (deviceBaseTopic == null)
  throw new ArgumentNullException($"No device found or no access to device with id {deviceIdToSubscribeTo}");

// publish message
string topicToPublish = deviceBaseTopic + devicePublishTopic;
await Publish_Application_Message(host, port, connectionProtocol, info, topicToPublish, devicePublishMessage);

// subscribe to topic and wait for messages
string topicToSubscribe = deviceBaseTopic + deviceSubscriptionTopic;
await Subscribe_Topic(host, port, connectionProtocol, info, topicToSubscribe);
