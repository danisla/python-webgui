import Queue
import thread
import time
from flask import Flask, jsonify, make_response, request
import json

from webgui import asynchronous_gtk_message



def api(port, message_queue):
    count = 0

    app = Flask(__name__)

    @app.route('/open', methods=['POST'])
    def open():
        url = request.args.get('url')
        message_queue.put(json.dumps(dict(action="open", data=url)))
        return jsonify({'message': 'Opening URL: %s' % url})

    @app.route('/reload', methods=['PUT'])
    def reload():
        message_queue.put(json.dumps(dict(action="reload")))
        return jsonify({'message': 'Forcing page reload'})

    @app.route('/shutdown', methods=['POST'])
    def shutdown():
        message_queue.put(json.dumps(dict(action="shutdown")))
        return jsonify({'message': 'Shutting down!'})

    app.run(port=port, debug=False)

def start_rest_api(port=8081, echo=False):
    print "Starting REST API on port: %d" % port

    message_queue = Queue.Queue()

    def rest_recv():
        if message_queue.empty():
            return None
        else:
            msg = message_queue.get()
            if echo: print '>>>', msg
            return msg

    t = thread.start_new_thread(api, (port, message_queue))

    return t, rest_recv
