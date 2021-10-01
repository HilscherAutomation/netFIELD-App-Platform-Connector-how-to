# netFIELD App Platform Connector how-to

# netFIELD App Platform Connector

The netFIELD App Platform Connector is your datas entrance to the cloud. Manage which data is published to the cloud, subscribe to MQTT topics and update your device firmware.

## Before you start
Before you start, make sure you have the following things:
- An onboarded, netFIELD ready device
- A user account with sufficient privileges to deploy containers to a device

## Installation
- If you haven't already, deploy a MQTT broker to your device. The netfield instance comes with a mosquitto container ready to deploy. If you want to deploy a different broker, create your own container with the appropriate docker image. The broker can be configured via environment variables or the container create options. Read the brokers documentation for how to set it up properly

- Deploy the netFIELD App Platform Connector container. 
    - Navigate to your device in your netFIELD instance, click on "containers" and select `netFIELD App Platform Connector` from the `Available Containers` tab.
    - The netFIELD App Platform Connector uses a system-wide configuration file for its MQTT settings. If you wish to connect to a different broker you can change these settings after deployment.
    - Click `Deploy` and allow the device a few minutes to download and install the container. You can check in on the status on the `Installed Containers` tab on your devices details page.


## Updating Firmware

The netFIELD App Platform Connector provides the functionality for you to update your devices operating system. Update images are provided by the netFIELD team and are ready for installation from within the netFIELD Portal.

- Navigate to your device details Page
- Select `netFIELD App Platform Connector` from the `Device Navigation` sidebar
- From the `Edge OS` tab, click on the version you want to deploy and confirm the action by clicking on `Deploy`
- Your device will send periodical progress reports, while it updates its firmware

## Managing MQTT subscriptions

Once netFIELD App Platform Connector is deployed, you can manage which topics it subsribes to. Data published to one of those topics are automatically send to the cloud via the netFIELD App Platform Connector. 

### Add a new subscription:
- Navigate to your devices details page, select `netFIELD App Platform Connector` from the `Device Navigation` sidebar and click on the `Topics` tab.
- Click `Add` 
- Chose a topic name you want to subscribe to
- Select the appropriate Quality of Service Level from the dropdown menu
- Click `Save`

### Managing Topic Subscriptions
You can change or delete subscriptions by clicking on the corresponding button next to the topics name.

### Viewing Topic Data
After subscribing to a topic, it is possible to view the latest message by simply clicking on a topic. Alternatively, you can use the button next to the topic.

## Sending Messages To The Device Broker
It is also possible, to publish arbitrary data from the cloud onto a devices broker.
- Navigate to your devices details page, select `netFIELD App Platform Connector` from the `Device Navigation` sidebar and click on the `Cloud To Device` tab
- Chose a topic name and a Quality of Service level
- Add the data you want to publish
- Click `Send`

The netFIELD App Platform Connector will receive your message and publish it to the broker

## Using The Built In REST API
Every container of the netFIELD App Platform Connector comes with a REST API. The functionality described above is accessible via this API as well. For ease of use and for documentation purposes a swagger client is provided. Simply point your browser to the the port defined in the `Container Create Options` (default is 5001) to access it.
Other containers deployed to your device can also access this API.

# Code Examples

In order to receive data published by the netFIELD App Platform Connector you can connect to the websocket server in the cloud. This allows any program to access published data remotely without the need to connect to a device directly.

The netFIELD App Platform Connector automatically chunks messages larger than 1MB. If messages are below that threshold, there are sent as is. The examples below are simply ones, no de-chunking mechanism is implementd. For a more detailed exmaple, see: URL

## C# Example

```C#
using System;
using System.Reactive.Concurrency;
using System.Reactive.Linq;

// external dependencies
// Json.NET: https://www.newtonsoft.com/json
using Newtonsoft.Json;
// https://github.com/Marfusios/websocket-client
using Websocket.Client;

namespace netFIELD_Portal_Web_UI.Helpers.WebSocketsClient
{
  /// <summary>
  /// WebSocket client to communicate with the netFIELD Platform Connector WebSocket.
  /// </summary>
  public class NetFIELDPlatformConnectorWebsocketClient
  {
    private WebsocketClient client;
    private Uri endpoint;
    private string authorization;
    private string clientId;

    /// <summary>
    /// Create a NetFIELDPlatformConnectorWebsocketClient instance.
    /// </summary>
    /// <param name="endpoint">WebSocket endpoint, e.g. wss://api.netfield.io/v1</param>
    /// <param name="authorization">Access token or API key.</param>
    /// <param name="pubMessageHandler">Handler to be called on receiving an update message on the WebSocket.</param>
    /// <param name="onErrorHandler">Handler to be called on errors.</param>
    /// <param name="onCloseHandler">Handler to be called on closing the connection.</param>
    /// <param name="unexpectedMessageHandler">Handler to be called on receiving an unexpected message.</param>
    public NetFIELDPlatformConnectorWebsocketClient(string endpoint, string authorization, Action<ResponseMessage> pubMessageHandler, Action<string> onErrorHandler, Action<string> onCloseHandler, Action<string> unexpectedMessageHandler)
    {
      this.endpoint = new Uri(endpoint);
      this.authorization = authorization;
      this.clientId = Guid.NewGuid().ToString(); // generate a unique client id
      this.client = new WebsocketClient(this.endpoint);
      this.client.ReconnectTimeout = TimeSpan.FromSeconds(5);

      this.client
     .MessageReceived
     .Where(msg => msg.Text != null)
     .ObserveOn(TaskPoolScheduler.Default)
     .Subscribe(msg =>
     {
       try
       {
         // deserialize JSON message
         NesMessage msgObj = JsonConvert.DeserializeObject<NesMessage>(msg.Text);
         switch (msgObj.type)
         {
           case "hello":
             // got a 'hello' response after successfully authenticating, do nothing
             Console.WriteLine("hello");
             break;
           case "sub":
             // got a 'sub' response after successfully subscribing to a topic, do nothing
             // Console.WriteLine("sub");
             break;
           case "ping":
             this._respondToHeartbeatPing();
             // Console.WriteLine("ping");
             break;
           case "pub":
             pubMessageHandler(msg);
             // Console.WriteLine("pub");
             break;
           default:
             // Got a message which was neither a 'hello', 'ping', 'sub' or 'pub' message;
             unexpectedMessageHandler(msg.Text);
             break;
         }
       }
       catch (Exception e)
       {
         Console.WriteLine(e);
         onErrorHandler(msg.Text);
       }
     });

      this.client.Start();
      _sayHello();
    }

    /// <summary>
    ///  Stop/close websocket connection
    /// </summary>
    internal void Close()
    {
      try
      {
        this.client.StopOrFail(System.Net.WebSockets.WebSocketCloseStatus.NormalClosure, "Closed from Client").Wait();
      }
      catch (Exception e)
      {
        Console.WriteLine(e.Message);
      }
    }

    /// <summary>
    /// Send a message by passing in an object which will be serialized before sending.
    /// </summary>
    /// <param name="data">data object to send.</param>
    public void SendObject(object data)
    {
      this.client.Send(JsonConvert.SerializeObject(data));
    }

    /// <summary>
    /// Subscribe to netFIELD Platform connector messages for the given device on the given topic.
    /// </summary>
    /// <param name="deviceId">deviceId of the device running netFIELD Platform connector.</param>
    /// <param name="topic">topic to subscribe to. This is the plaintext topic, it will automatically be converted to a base64 string.</param>
    public void SubscribeToTopic(string deviceId, string topic)
    {
      var topicAsBase64 = Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes(topic));
      var subscribePayload = new
      {
        id = this.clientId,
        path = $"/devices/{deviceId}/platformconnector/{topicAsBase64}",
        type = "sub"
      };
      this.SendObject(subscribePayload);
    }


    /// <summary>
    /// Send a 'hello' message according the nes protocol which authenticates this client.
    /// https://github.com/hapijs/nes/blob/master/PROTOCOL.md#Hello
    /// </summary>
    private void _sayHello()
    {
      var helloPayload = new
      {
        type = "hello",
        id = this.clientId,
        version = "2",
        auth = new
        {
          headers = new
          {
            authorization = this.authorization,
          },
        },
      };
      this.SendObject(helloPayload);
    }

    /// <summary>
    /// Send a heartbeat keep-alive ping response according to the nes protocol.
    /// https://github.com/hapijs/nes/blob/master/PROTOCOL.md#Heartbeat
    /// </summary>
    private void _respondToHeartbeatPing()
    {
      var pingResponse = new
      {
        type = "ping",
        id = this.clientId,
      };
      this.SendObject(pingResponse);
    }
  }

  /// <summary>
  /// Represents message received on the WebSocket according to the nes protocol.
  /// https://github.com/hapijs/nes/blob/master/PROTOCOL.md
  /// </summary>
  public class NesMessage
  {
    [JsonProperty("type")]
    public string type { get; set; }

    [JsonProperty("message")]
    public NetfieldPlatfromConnectorUpdateMessage message { get; set; }
  }

  /// <summary>
  /// Represents netFIELD Platform connector update message received on the WebSocket.
  /// 
  /// Example:
  /// {
  ///   "createdAt":1569424627376,
  ///   "topic":"/fromDeviceToCloud",
  ///   "data":"payload, cnt 14"
  /// }
  /// </summary>
  public class NetfieldPlatfromConnectorUpdateMessage
  {
    [JsonProperty("createdAt", NullValueHandling = NullValueHandling.Ignore)]
    public DateTime CreatedAt { get; set; }

    [JsonProperty("topic", NullValueHandling = NullValueHandling.Ignore)]
    public string Topic { get; set; }

    [JsonProperty("chunk", NullValueHandling = NullValueHandling.Ignore)]
    public string Chunk { get; set; }

    [JsonProperty("data", NullValueHandling = NullValueHandling.Ignore)]
    public dynamic Data { get; set; }
  }
}
```

## Javascript Example

```Javascript
/* Polyfill Websocket and btoa */
if (typeof WebSocket !== 'function') {
  // WebSocket is not globally defined, probably running in node.js
  var WebSocket = require('ws');
}
if (typeof btoa !== 'function') {
  // btoa is not globally defined, probably running in node.js
  var btoa = require('btoa');
}


/**
 * WebSocket client to communicate with the netFIELD Proxy WebSocket.
 *
 * @class NetFieldProxyWebSocketClient
 */
class NetFieldProxyWebSocketClient {
  /**
   *Creates an instance of NetFieldProxyWebSocketClient.
   * @param {string} endpoint - WebSocket endpoint, e.g. wss://api.netfield.io/v1
   * @param {string} authorization - Access token or API key.
   * @param {string} deviceId - deviceId of the device running netFIELD Proxy.
   * @param {string} topic -
   *   topic to subscribe to (plaintext, converted to base64 automatically)
   * @param {Object} [handlers] - handlers for events and messages
   * @param {function} [handlers.pubMessageHandler=console.log] -
   *   Handler to be called on receiving a netFIELD Proxy update message on the WebSocket.
   * @param {function} [handlers.errorHandler=console.error] -
   *   Handler to be called on errors.
   * @param {function} [handlers.closeHandler=console.log] -
   *   Handler to be called on closing the connection.
   * @param {function} [handlers.unexpectedMessageHandler=console.warn] -
   *   Handler to be called on receiving an unexpected message.
   */
  constructor(
    endpoint,
    authorization,
    deviceId,
    topic,
    {
      pubMessageHandler = console.log,
      errorHandler = console.error,
      closeHandler = console.log,
      unexpectedMessageHandler = console.warn,
    },
  ) {
    this.endpoint = endpoint;
    // generate a clientId
    this.clientId = (Math.random() + 1).toString(36).substring(7);
    this.deviceId = deviceId;
    this.topic = topic;
    this.authorization = authorization;
    this.pubMessageHandler = pubMessageHandler;
    this.errorHandler = errorHandler;
    this.closeHandler = closeHandler;
    this.unexpectedMessageHandler = unexpectedMessageHandler;
    this.wsClient = this._initializeWebSocketClient();

    this.subscribeToTopic = this.subscribeToTopic.bind(this);
    this.send = this.send.bind(this);
    this.sendObject = this.sendObject.bind(this);
    this.close = this.close.bind(this);
  }

  /**
   * Initialize the WebSocket client.
   *
   * @access private
   *
   * @returns { WebSocket } WebSocket client.
   */
  _initializeWebSocketClient() {
    const client = new WebSocket(this.endpoint);
    client.onmessage = this._messageHandler.bind(this);
    client.onerror = this.errorHandler;
    client.onclose = this.closeHandler;
    client.onopen = this._sayHello.bind(this);
    return client;
  }

  /**
   * Handler to be invoked on receiving a message on the WebSocket.
   *
   * @param { WebSocket.MessageEvent } event - WebSocket message event.
   * @param { WebSocket.Data } event.data - WebSocket message data.
   *
   * @access private
   */
  _messageHandler({ data }) {
    try {
      const dataObj = JSON.parse(data);
      const { type, message, payload } = dataObj;
      if (payload && payload.error) {
        this.errorHandler(data);
        return;
      }
      switch (type) {
        case 'hello':
          // got a 'hello' response after successfully authenticating, subscribing
          this.subscribeToTopic(this.deviceId, this.topic);
          break;
        case 'sub':
          // got a 'sub' response after successfully subscribing
          // -> do nothing and wait for 'pub' messages
          break;
        case 'ping':
          // got a keep-alive 'ping' heartbeat from the server
          this._respondToHeartbeatPing();
          break;
        case 'pub':
          // got a 'pub' message from the server
          this.pubMessageHandler(message);
          break;
        default:
          this.unexpectedMessageHandler(data);
          break;
      }
    } catch (error) {
      this.errorHandler(error);
    }
  }

  /**
   * Subscribe to netFIELD proxy messages for the given device on the given topic.
   *
   * @param {string} deviceId - deviceId of the device running netFIELD Proxy.
   * @param {string} topic - topic to subscribe to (plaintext, converted to base64 automatically)
   */
  subscribeToTopic(deviceId, topic) {
    const topicAsBase64 = btoa(topic);
    const subscribePayload = {
      id: this.clientId,
      path: `/devices/${deviceId}/netfieldproxy/${topicAsBase64}`,
      type: 'sub',
    };
    this.sendObject(subscribePayload);
  }

  /**
   * Send a string message.
   *
   * @param {string} dataString - string to send.
   */
  send(dataString) {
    const { wsClient } = this;
    if (wsClient && wsClient.readyState === wsClient.OPEN) {
      wsClient.send(dataString);
    }
  }

  /**
   * Send a message by passing in an object which will be serialized before sending.
   *
   * @param {Object} dataObj - data object to send.
   */
  sendObject(dataObj) {
    this.send(JSON.stringify(dataObj));
  }

  /**
   * Close the connection to the WebSocket.
   *
   * @param {number} [code]
   * @param {string} [data]
   */
  close(code, data) {
    const { wsClient } = this;
    if (wsClient && wsClient.readyState === wsClient.OPEN) {
      wsClient.close(code, data);
    }
  }

  /**
   * Send a 'hello' message according the nes protocol which authenticates this client.
   *
   * https://github.com/hapijs/nes/blob/master/PROTOCOL.md#Hello
   *
   * @access private
   */
  _sayHello() {
    const helloPayload = {
      type: 'hello',
      auth: {
        headers: {
          authorization: this.authorization,
        },
      },
      id: this.clientId,
      version: '2',
    };
    this.sendObject(helloPayload);
  }

  /**
   * Send a heartbeat keep-alive ping response according to the nes protocol.
   *
   * https://github.com/hapijs/nes/blob/master/PROTOCOL.md#Heartbeat
   *
   * @access private
   */
  _respondToHeartbeatPing() {
    const pingResponsePayload = {
      id: this.clientId,
      type: 'ping',
    };
    this.sendObject(pingResponsePayload);
  }
}

// usage example

/**
 * Handler to be called on receiving a netFIELD Proxy update message on the WebSocket.
 *
 * @param {Object} netFieldProxyMessage - netFIELD Proxy update message object
 * @param {number} netFieldProxyMessage.createdAt - unix timestamp in milliseconds
 * @param {string} netFieldProxyMessage.topic - topic (plain text, not base64-encoded)
 * @param {string} netFieldProxyMessage.data - the message content
 */
const myPubMessageHandler = (netFieldProxyMessage) => {
  // do something with the received message
  console.log('Received a netFIELD proxy message:', netFieldProxyMessage);
};

/**
 * Handler called on errors.
 *
 * Error causes:
 * * WebSocket connection errors.
 * * Error parsing a received message.
 * * Invalid credentials.
 *
 * @param {*} error
 */
const myErrorHandler = (error) => {
  // do something on receiving an error
  console.error('An error occured:', error);
};

/**
 * Handler to be called on receiving an unexpected message.
 *
 * @param {string} message
 */
const myUnexpectedMessageHandler = (message) => {
  // do something on receiving an unexpected message
  console.warn('Received an unexpected message:', message);
};

/**
 * Handler to be called on closing the connection.
 *
 * @param {WebSocket.CloseEvent} event
 */
const myCloseHandler = (event) => {
  console.log('Connection to WebSocket closed:', event);
};

const handlers = {
  pubMessageHandler: myPubMessageHandler,
  errorHandler: myErrorHandler,
  unexpectedMessageHandler: myUnexpectedMessageHandler,
  closeHandler: myCloseHandler,
};

const endpoint = 'wss://api.netfield.io';
const deviceId = '{deviceId}';
const topic = '{topic}';
const authorization = '{authorization}'; // API Key or User Token with viewDeviceDetails permission 

console.log(
  `Initializing connection to WebSocket at ${endpoint} and subscribing to topic ${topic} on device ${deviceId} ...`,
);

const client = new NetFieldProxyWebSocketClient(
  endpoint,
  authorization,
  deviceId,
  topic,
  handlers,
);

const keepConnectionOpenForSeconds = 60;
console.log(`Connection initialized, keeping open for ${keepConnectionOpenForSeconds} s ...`);
setTimeout(client.close, keepConnectionOpenForSeconds * 1000);

```
