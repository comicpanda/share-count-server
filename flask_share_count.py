from flask import Flask, jsonify, request
import grequests, re, json, logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
default_logger = logging.getLogger('werkzeug')

FACEBOOK = 'https://api.facebook.com/method/links.getStats?urls=%s&format=json'
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

    default_logger.debug('target_url: ' + target_url)

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
            grequests.get(FACEBOOK % (target_url), timeout=5),
            grequests.post(GOOGLE_PLUS, data=json_param, timeout=5)
        )
    except:
        return jsonify(result='error', total=-1)

    responses = grequests.map(requests)

    counts = (
        parse_facebook(responses[0]),
        parse_googleplus(responses[1])
    )

    default_logger.debug(counts)

    total_count = 0
    for count in counts:
        total_count += count

    default_logger.debug('total_count: %d' % (total_count))

    return jsonify(result='success', total= total_count)

@app.errorhandler(500)
def internal_server_error(error):
    default_logger.error(error)
    return jsonify(result='error', total=-1)

def parse_facebook(res):
    facebook_data = res.json()[0]
    return facebook_data['share_count'] + facebook_data['like_count']

def parse_googleplus(res):
    return int(res.json()[0]['result']['metadata']['globalCounts']['count'])

if __name__ == '__main__':
    file_handler = RotatingFileHandler('/comicpanda/logs/share-count.log', maxBytes=1024 * 1024 * 100)
    file_handler.setLevel(logging.INFO)

    default_logger.setLevel(logging.INFO)
    default_logger.addHandler(file_handler)

    app.run(host='0.0.0.0', port=7300)
