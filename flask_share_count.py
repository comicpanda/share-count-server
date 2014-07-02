from flask import Flask, jsonify, request
import grequests, re, json, logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

FACEBOOK = 'https://api.facebook.com/method/links.getStats?urls=%s&format=json'
TWITTER = 'http://urls.api.twitter.com/1/urls/count.json?url=%s&callback=count'
REDDIT = 'http://buttons.reddit.com/button_info.json?url=%s'
STUMBLEUPON = 'http://www.stumbleupon.com/services/1.01/badge.getinfo?url=%s'
PINTEREST = 'http://widgets.pinterest.com/v1/urls/count.json?source=6&url=%s'
GOOGLE_PLUS = 'https://clients6.google.com/rpc?key=AIzaSyCKSbrvQasunBoV16zDH9R33D88CeLr9gQ'

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/ping')
def ping():
    return 'pong'

@app.route('/count')
def total_count():
    target_url = request.args.get('url')

    app.logger.debug('target_url: ' + target_url)

    params = []
    param = {}
    param['method'] = 'pos.plusones.get'
    param['id'] = 'p'
    param['params'] = {}
    param['params']['nolog'] = True
    param['params']['id'] = target_url
    param['params']['source'] = 'widget'
    param['params']['userId'] = '@viewer'
    param['params']['groupId'] = '@self'
    param['jsonrpc'] = '2.0'
    param['key'] = 'p'
    param['apiVersion'] = 'v1'
    params.append(param)

    json_param = json.dumps(params)

    try:
        requests = (
            grequests.get(FACEBOOK % (target_url)),
            grequests.get(TWITTER % (target_url)),
            grequests.get(REDDIT % (target_url)),
            grequests.get(STUMBLEUPON % (target_url)),
            grequests.get(PINTEREST % (target_url)),
            grequests.post(GOOGLE_PLUS, data=json_param)
        )
    except:
        return jsonify(result='error', total=-1)

    responses = grequests.map(requests)

    counts = (
        parse_facebook(responses[0]),
        parse_twitter(responses[1]),
        parse_reddit(responses[2]),
        parse_stumbleupon(responses[3]),
        parse_pinterest(responses[4]),
        parse_googleplus(responses[5])
    )

    app.logger.debug(counts)

    total_count = 0
    for count in counts:
        total_count += count

    app.logger.debug('total_count: %d' % (total_count))

    return jsonify(result='success', total= total_count)

def parse_facebook(res):
    facebook_data = res.json()[0]
    return facebook_data['share_count'] + facebook_data['like_count']

def parse_twitter(res):
    m = re.search(r'{.+}', res.content)
    raw_data = m.group(0)
    return json.loads(raw_data)['count']

def parse_reddit(res):
    json_data = res.json()
    if 'data' in json_data and 'children' in json_data['data'] and json_data['data']['children']:
        return res.json()['data']['children'][0]['data']['score']
    return 0

def parse_stumbleupon(res):
    if 'views' in res.json()['result']:
        return int(res.json()['result']['views'])
    return 0

def parse_pinterest(res):
    m = re.search(r'{.+}', res.content)
    return json.loads(m.group(0))['count']

def parse_googleplus(res):
    return int(res.json()[0]['result']['metadata']['globalCounts']['count'])

if __name__ == '__main__':    
    file_handler = RotatingFileHandler('/comicpanda/logs/share-count.log', maxBytes=1024 * 1024 * 100, backupCount=20)
    file_handler.setLevel(logging.ERROR)
    app.logger.addHandler(file_handler)

    app.run(host='0.0.0.0', port=7300)
