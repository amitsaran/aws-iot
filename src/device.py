
import ssl
import csv
import random
import json
import time
import os


from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from time import sleep
from datetime import date, datetime


def on_message_receive(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")

CLIENT_NAME = "test-client-1"
TOPIC = "test-iot-topic-1"

# Broker path is under AWS IoT > Settings (at the bottom left)
BROKER_PATH = ""

# RSA 2048 bit key: Amazon Root CA 1 found here:
# https://docs.aws.amazon.com/iot/latest/developerguide/managing-device-certs.html
ROOT_CA_PATH = './AmazonRootCA1.pem'

# These two keys are downloaded from the AWS IoT Console
PRIVATE_KEY_PATH = './private.pem.key'
CERTIFICATE_PATH = './certificate.pem.crt'


IoTclient = AWSIoTMQTTClient(CLIENT_NAME)
IoTclient.configureEndpoint(BROKER_PATH, 8883)
IoTclient.configureCredentials(
    ROOT_CA_PATH, 
    PRIVATE_KEY_PATH, 
    CERTIFICATE_PATH
)

# Allow the device to queue infinite messages
IoTclient.configureOfflinePublishQueueing(-1)

# Number of messages to send after a connection returns
IoTclient.configureDrainingFrequency(2)  # 2 requests/second

# How long to wait for a [dis]connection to complete (in seconds)
IoTclient.configureConnectDisconnectTimeout(10)

# How long to wait for publish/[un]subscribe (in seconds)
IoTclient.configureMQTTOperationTimeout(5) 


IoTclient.connect()
#time.sleep(5)
#IoTclient.publish(TOPIC, json.dumps({"message":"connected"}), 0)

loopCount = 0
while True:
#while (loopCount < 10):
    IoTclient.subscribe(TOPIC, 1, on_message_receive)
    message = {}
    message['message'] = "Hello from MQQT client"
    message['sequence'] = loopCount
    messageJson = json.dumps(message)
    IoTclient.publish(TOPIC, messageJson, 1)
    loopCount += 1
    time.sleep(1)
