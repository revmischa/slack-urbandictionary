import json
import datetime
import requests
import random
import boto3
from urllib.parse import parse_qs
from pprint import pprint

# AWS SSM encrypted parameter store
ssm = boto3.client('ssm', region_name='ap-southeast-1')
def get_ssm_param(param_name: str) -> str:
    """Get an encrypted AWS Systems Manger secret."""
    response = ssm.get_parameters(
        Names=[param_name],
        WithDecryption=True,
    )
    if not response['Parameters'] or not response['Parameters'][0] or not response['Parameters'][0]['Value']:
        raise Exception(f"Configuration error: missing AWS SSM parameter: {param_name}")
    return response['Parameters'][0]['Value']

SLACK_OAUTH_CLIENT_ID = get_ssm_param('ud_slack_oauth_client_id')
SLACK_OAUTH_CLIENT_SECRET = get_ssm_param('ud_slack_oauth_client_secret')


def respond(err=None, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def slack_slash(event):
    params = parse_qs(event['body'])
    # command = params['command'][0]
    # channel = params['channel_name'][0]
    text = params['text'][0]

    res = requests.get('http://api.urbandictionary.com/v0/define', params={'term': text})

    if res.status_code != 200:
        return respond(res={
            'response_type': 'ephemeral',
            'text': f'Unknown word: {text}'
        })

    # parse definition
    ud_res = res.json()
    definitions = ud_res['list']
    if not definitions:
        return respond(res={
            'response_type': 'ephemeral',
            'text': f'Unknown word: {text}'
        })

    # definition = random.choice(definitions)
    definition = definitions[0]

    return respond(res={
        'response_type': 'in_channel',
        'text': f'Urban dictionary definition of "{text}":',
        'attachments': [
            {
                "mrkdwn": False,
                "title": "Definition",
                "title_link": definition['permalink'],
                "text": definition['definition'],
            },
            {
                "mrkdwn": False,
                "title": "Example",
                "text": definition['example'],
            }
        ]
    })

def oauth_begin(event):
    return {
        'statusCode': 302,
        'body': "Redirecting...",
        'headers': {
            'Location': 'https://slack.com/oauth/authorize?client_id=2716024371.296705110721&scope=commands',
        },
    }


def oauth(event):
    args = event['queryStringParameters']
    code = args['code']
    print(f"code; {code}")
    # get auth token
    res = requests.get('https://slack.com/api/oauth.access', params={
        'code': code,
        'client_id': SLACK_OAUTH_CLIENT_ID,
        'client_secret': SLACK_OAUTH_CLIENT_SECRET,
        'redirect_uri': 'https://singapi.mischa.lol/udv1/oauth',
    }).json()

    print(res)
    return "Success!"

    return {
        'statusCode': 302,
        'body': "Installed!",
        'headers': {
            'Location': 'https://github.com/revmischa/slack-urbandictionary#usage',
        },
    }

def handler(event, context):
    if event['path'] == '/oauth':
        return oauth(event)
    elif event['path'] == '/install':
        return oauth_begin(event)
    elif event['path'] == '/':
        return slack_slash(event)
    else:
        return respond(err=f"unknown path {event['path']}")

if __name__ == 'main':
    handler({})
