import os
import re
import json
import boto3
import requests
from base64 import b64decode
 
ENCRYPTED_GA_SECRET = os.environ['ga_secret']
DECRYPTED_GA_SECRET = boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTED_GA_SECRET))['Plaintext']

def send_email(html_email, plaintext_email, reply_to):
    try:
        ses = boto3.client('ses')
        response = ses.send_email(
            Source='fmcorey@gmail.com',
            Destination={
                'ToAddresses': ['fmcorey@gmail.com'],
                'CcAddresses': [],
                'BccAddresses': []
            },
            Message={
                'Subject': {
                    'Data': 'Contact form message - fernandomc.com',
                },
                'Body': {
                    'Text': {
                        'Data': plaintext_email
                    },
                    'Html': {
                        'Data': html_email
                    }
                }
            },
            ReplyToAddresses=[
                reply_to,
            ]
        )
        print response
    except Exception as e:
        print 'Failed to send message via SES'
        print e.message
        raise e

def validate_inputs(post_json):
    pattern = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
    params = ("message","name","email","captcha")
    # Check post_json for missing params
    if not all (param in post_json for param in params):
        return ['Parameter missing', 0]
    else:
        print('All params present in JSON POST')
    # Check for emtpty strings
    for i in post_json:
        if not post_json[i]:
            return ['content of {} missing'.format(i), 0]
        else:
            print 'All params contain text'
    # Validate email
    if not pattern.match(post_json['email']):
        return ['invalid email', 0]
    return ['inputs validated', 1]

def validate_captcha(captcha_response):
    url = 'https://www.google.com/recaptcha/api/siteverify'
    ga_secret = DECRYPTED_GA_SECRET
    response = json.loads(requests.post(
        url, 
        data={
            'secret': ga_secret, 
            'response':captcha_response
        }
    ).text)
    return response['success']

def lambda_handler(event, context):
    status = 'success'
    print event
    post_json = json.loads(event['body'])
    print 'post_json:'
    print post_json
    message = post_json['message']
    name = post_json['name']
    email = post_json['email']
    captcha_response = post_json['captcha']
    v = validate_inputs(post_json)
    if v[1] == 0:
        status = v[0]
    else:
        print v[0]
    if not validate_captcha(captcha_response):
        status = 'Captcha Invalid'
    if status == 'success':
        print 'sending email'
        send_email(message, message, email)
    res_body = """
    {{
        "name":"{0}",
        "email":"{1}",
        "message":"{2}",
        "status":"{3}"
    }}""".format(name, email, message, status)
    print 'res_body'
    print res_body
    return {
        "statusCode":200,
        "headers": {"Access-Control-Allow-Origin":"*"},
        "body": res_body
}
 