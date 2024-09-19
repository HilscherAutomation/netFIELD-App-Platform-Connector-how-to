# How-to

# netFIELD App Platform Connector

The netFIELD App Platform Connector is your gateway to the cloud. It allows you to manage which data is published to the cloud, subscribe to MQTT topics, receive data from the Data Service and publish it to the local device’s MQTT broker, as well as update your device’s firmware.

# netFIELD Data-Service

The netFIELD Data Service is a cloud MQTT broker that allows you to securely receive data from your device or send data to your device from the cloud. You can easily connect to the broker via an MQTT client using either the MQTTs or MQTT over WebSocket protocol.

## Before you start
Before you start, make sure you have the following things:
- An onboarded, netFIELD ready device
- A user account with sufficient privileges to deploy containers to a device

## Installation
- If you haven't already, deploy a MQTT broker to your device. The netFIELD instance comes with a [mosquitto](https://mosquitto.org/) container ready to deploy. If you want to deploy a different broker, create your own container with the appropriate docker image. The broker can be configured via environment variables or the container create options. Read the brokers documentation for how to set it up properly

- Deploy the netFIELD App Platform Connector container.
    - Navigate to your device in your netFIELD instance, click on "containers" and select `netFIELD App Platform Connector` from the `Available Containers` tab.
    - The netFIELD App Platform Connector uses a system-wide configuration file for its MQTT settings. If you wish to connect to a different broker you can change these settings after deployment.
    - Click `Deploy` and allow the device a few minutes to download and install the container. You can check in on the status on the `Installed Containers` tab on your devices details page.

## Updating Firmware

The netFIELD App Platform Connector provides the functionality for you to update your devices operating system. Update images are provided by the netFIELD team and are ready for installation from within the netFIELD Portal.

- Navigate to your device details page
- Select `netFIELD App Platform Connector` from the `Device Navigation` sidebar
- From the `Edge OS` tab, click on the version you want to deploy and confirm the action by clicking on `Deploy`
- Your device will send periodical progress reports, while it updates its firmware

## MQTT message management

In this section, you will find a detailed description of MQTT message management (sending and receiving), along with various sample codes for different programming languages.

### [Managing MQTT subscriptions](device-container-examples\README.md)

### [Sending Messages To The Device Broker](api-key-examples\README.md)

## Using The Built In REST API
Every container of the netFIELD App Platform Connector comes with a REST API. The functionality described above is accessible via this API as well. For ease of use and for documentation purposes a swagger client is provided. Simply point your browser to the port defined in the `Container Create Options` (default is 5001) to access it.

Other containers deployed to your device can also access this API.

