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
print(AWS_ACCESS_KEY_ID)
print(AWS_SECRET_ACCESS_KEY)
print(REGION_NAME)

iot_client = boto3.client('iot',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION_NAME)

response = iot_client.describe_endpoint(
    endpointType='iot:Data-ATS'
)

print(response['endpointAddress'])