import json
import datetime
import requests
from urllib.parse import parse_qs


def respond(err=None, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def handler(event, context):
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


if __name__ == 'main':
    handler({})
