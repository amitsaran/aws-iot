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
THING_NAME = 'test-thing-1'
TOPIC_NAME = "test-iot-topic-1"

thingArn = ''
# thingId = ''

iot_client = boto3.client('iot',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION_NAME)

# create policy
policy_doc = json.dumps(POLICY_DOCUMENT)
response = iot_client.create_policy(
    policyName = POLICY_NAME,
    policyDocument = policy_doc
)

# crete thing
thing_response = iot_client.create_thing(
    thingName = THING_NAME
)

# get the things arn and id
data = json.loads(json.dumps(thing_response, sort_keys=False, indent=4))
for element in data: 
    if element == 'thingArn':
        thingArn = data['thingArn']
    # elif element == 'thingId':
    #     thingId = data['thingId']

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
    #elif element == 'certificateId':
    #    certificateId = data['certificateId']
        
with open('public.pem.key', 'w') as outfile:
    outfile.write(public_pem_key)
with open('private.pem.key', 'w') as outfile:
    outfile.write(private_pem_key)
with open('certificate.pem.crt', 'w') as outfile:
    outfile.write(certificate_pem_crt)

# attach policy to certificate
response = iot_client.attach_policy(
    policyName = POLICY_NAME,
    target = certificateArn
)

#attach thing to certificate
response = iot_client.attach_thing_principal(
    thingName = THING_NAME,
    principal = certificateArn
)

sns_client = boto3.client('sns',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION_NAME)

# create SNS topic
SNS_TOPIC_NAME='iot-notification'
sns_topic_response = sns_client.create_topic(Name=SNS_TOPIC_NAME)
topic_arn = sns_topic_response['TopicArn']
# print(topic_arn)

# add email subscribers
EMAIL_ID = 'amit_k_saran@yahoo.com'
response = sns_client.subscribe(
    TopicArn=topic_arn,
    Protocol='email',
    Endpoint=EMAIL_ID
)

iam_client = boto3.client('iam',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION_NAME)

# create role
response = iam_client.create_role(
    Path='/service-role/',
    RoleName='test-iot-role-1',
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
# print(response)
roleArn = response['Role']['Arn']

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
# print(policyArn)
iam_client.attach_role_policy(
    RoleName='test-iot-role-1',
    PolicyArn=policyArn
)

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

response = iot_client.describe_endpoint(
    endpointType='iot:Data-ATS'
)
print(response['endpointAddress'])
