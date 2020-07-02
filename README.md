# aws-iot
## What is IoT?
The Internet of things is a system of interrelated computing devices, mechanical and digital machines with the ability to transfer data over a network without requiring human-to-human or human-to-computer interaction.
It is about extending the power of the internet beyond computers and smartphones to a whole range of other things, processes, and environments.

## What is AWS IoT?
AWS IoT enables secure, bi-directional communication between Internet-connected things and the AWS cloud. This enables the collection of telemetry data from multiple devices and store and analyze the data.

## Example: 
The following example registers a single device in AWS IOT; Creates a rule to publish a message to an SNS topic; SNS sends a notification to the subscribed email address.

### Architectue
#### ![alt text](./assets/images/iot-first-device.svg)

Anyone can log in to his/her AWS account and create the required infrastructure for the example above. But I have chosen to create the infrastructure using AWS SDK for Python3.

### Code - IOT Infrastricture

AWS provides SDK in all major programming language and Python is used here to develop the required infrastructure. AWS provides "AWS SDK for Python" to develop and manage AWS services and "AWS IOT SDK for Python" to develop and manage AWS IOT services. 

create_infra.py creates the required IoT Infrastructure as described in the architecture diagram. device.py mimics a configurd device and publishes/receives messages to the IoT endpoint. A detailed explanation is given below:

1. "IoT Thing" - Refer to the Architecture Diagram above
    * Import statements and secret key
        <pre><code>
            import boto3
            import json
            AWS_ACCESS_KEY_ID = ''
            AWS_SECRET_ACCESS_KEY = ''
            REGION_NAME = ''
            with open('./secret.key') as json_file: 
                data = json.load(json_file)
                AWS_ACCESS_KEY_ID = data['AWS_ACCESS_KEY_ID']
                AWS_SECRET_ACCESS_KEY = data['AWS_SECRET_ACCESS_KEY']
                REGION_NAME = data['REGION_NAME']
        </pre></code>
    * Get the IoT client.
        <pre><code>
        AWS_ACCESS_KEY_ID = <<IAM access key id>>
        AWS_SECRET_ACCESS_KEY = <<IAM secret key>>
        REGION_NAME = ''
        iot_client = boto3.client('iot',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=REGION_NAME)
        </pre></code>
    * Create a Thing. THING_NAME is important as it will be used to attach the certificate to the thing.
        <pre><code>
        THING_NAME = 'test-thing-1'
        response = iot_client.create_thing(
            thingName = THING_NAME
        )
        </pre></code>
    * Create a Certificate and store the "certificateArn", which will be used to attach the policy to the certificate.
        <pre><code>
        # create key and certificate, which will be used for authentication
        cert_response = iot_client.create_keys_and_certificate(
            setAsActive = True
        )
        public_pem_key = ""
        private_pem_key = "" 
        certificate_pem_crt = ""
        certificateArn = ""
        data = json.loads(json.dumps(cert_response, sort_keys=False, indent=4))
        for element in data: 
            if element == 'certificateArn':
                certificateArn = data['certificateArn']
            elif element == 'keyPair':
                public_pem_key = data['keyPair']['PublicKey']
                private_pem_key = data['keyPair']['PrivateKey']
            elif element == 'certificatePem':
                certificate_pem_crt = data['certificatePem']
                
        with open('public.pem.key', 'w') as outfile:
            outfile.write(public_pem_key)
        with open('private.pem.key', 'w') as outfile:
            outfile.write(private_pem_key)
        with open('certificate.pem.crt', 'w') as outfile:
            outfile.write(certificate_pem_crt)
        </pre></code>
    * Create a Policy to be able to connect to AWS IOT and publish/subscribe messages. POLICY_NAME will be used to attach the policy to the certificate
        <pre><code>
            POLICY_NAME = 'test-policy-1'
            POLICY_DOCUMENT = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": "iot:*",
                        "Resource": "*"
                    }
                ]
            }

            policy_doc = json.dumps(POLICY_DOCUMENT)
            response = iot_client.create_policy(
                policyName = POLICY_NAME,
                policyDocument = policy_doc
            )
        </pre></code>
    * Attach the Policy to the Certificate
        <pre><code>
        response = iot_client.attach_policy(
            policyName = POLICY_NAME,
            target = certificateArn
        )
        </pre></code>
    * Attach the Certificate to the Thing:
        <pre><code>
        response = iot_client.attach_thing_principal(
            thingName = THING_NAME,
            principal = certificateArn
        )
        </pre></code>
    * Create an IoT Rule. The prerequisite for this is the SNS topic, which will be created in the next section.
      * Get the IAM client
            <pre><code>
            iam_client = boto3.client('iam',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=REGION_NAME)
            </pre></code>
      * Create IAM Role and capture the role ARN, which will be used during the creation of rule. Role name will be used to attach the policy with it.
        <pre><code>

                IAM_ROLE_NAME = 'test-iot-role-1'

                response = iam_client.create_role(
                    Path='/service-role/',
                    RoleName=IAM_ROLE_NAME,
                    AssumeRolePolicyDocument=json.dumps({
                        "Version":"2012-10-17",
                        "Statement":[{
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "iot.amazonaws.com"
                            },
                            "Action": "sts:AssumeRole"
                        }]
                    })
                )
                roleArn = response['Role']['Arn']

        </pre></code>
            
      * Create IAM Policy and capture the policy ARN, which will be used to attach the newly created policy with the IAM role.
        <pre><code>
        response = iam_client.create_policy(
            PolicyName='test-iot-policy-1',
            PolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": {
                    "Effect": "Allow",
                    "Action": "sns:Publish",
                    "Resource": topic_arn
                }
            })
                                                    )

        policyArn = response['Policy']['Arn']
        </pre></code>
      * Attach IAM Policy to the Role
        <pre><code>
        iam_client.attach_role_policy(
            RoleName=IAM_ROLE_NAME,
            PolicyArn=policyArn
        )
        </pre></code>
    <pre><code>
        # create rule
        sql_str = "SELECT * FROM \'" + TOPIC_NAME + "\'"
        # print(sql_str)
        response = iot_client.create_topic_rule(
            ruleName='iotrule2',
            topicRulePayload={
                'awsIotSqlVersion': '2016-03-23',       
                'sql': sql_str,
                'description': 'test',
                'actions': [{
                    'sns': {
                            'targetArn': topic_arn,
                            'roleArn': roleArn,
                            'messageFormat': 'RAW'
                        }
                }],
                'ruleDisabled': False        
            }
        )
    </pre></code>
2. AWS Service - SNS
    * Get the SNS client
        <pre><code>
        sns_client = boto3.client('sns',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=REGION_NAME)
        </pre></code>  
    * Create an SNS topic. Stoe the topic ARN(Amazon Resource Name), which will be used in three subsequent calls.(Creating a subscription, Policy, Rule)
        <pre><code>
        # create SNS topic
        SNS_TOPIC_NAME='iot-notification'
        sns_topic_response = sns_client.create_topic(Name=SNS_TOPIC_NAME)
        topic_arn = sns_topic_response['TopicArn']
        </pre></code>
    * Subscribe an email to be able to receive notification from SNS topic.
        <pre><code>
        EMAIL_ID = <<email id>>
        response = sns_client.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=EMAIL_ID
        )
        </pre></code>
    
3. Subscribers: 
   Nothing much to be done here. After "create_infra.py" is run, an email will be received to confirm the subscription. After confirmation, the SNS topic will be able to send notifications to the email id.
4. get the AWS IoT ATS signed data endpoint, which will be used by the MQTT client to publish/subscribe messages.
    <pre><code>
    response = iot_client.describe_endpoint(
        endpointType='iot:Data-ATS'
    )
    print(response['endpointAddress'])
    </pre></code>

### Code - MQQT Client - uses AWS IoT Python SDK
1. Import statements:
   <pre><code>
    import ssl
    import csv
    import random
    import json
    import time
    import os
    from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
    from time import sleep
    from datetime import date, datetime
   </pre></code>
2. Connect to the AWS Iot Device Gateway endpoint using the certificates created/downloaded during the creation of the IoT infrasture 
   <pre><code>
    CLIENT_NAME = "test-client-1"
    TOPIC = "test-iot-topic-1"
    # Broker path is under AWS IoT > Settings (at the bottom left)
    BROKER_PATH = "a9z45ceeh7nmy-ats.iot.us-east-1.amazonaws.com"
    # RSA 2048 bit key: Amazon Root CA 1 found here:
    # https://docs.aws.amazon.com/iot/latest/developerguide/managing-device-certs.html
    ROOT_CA_PATH = './AmazonRootCA1.pem'
    # These two keys are downloaded from the AWS IoT    
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
   </pre></code>
3. Keep publishing messages to the IoT topic. Also subscribe to the same topic with a callback function. If everything is configured properly, you should receive these messages in the subscribed email id.
   <pre><code>
    def on_message_receive(client, userdata, message):
        print("Received a new message: ")
        print(message.payload)
        print("from topic: ")
        print(message.topic)
        print("--------------\n\n")

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
   </pre></code>


