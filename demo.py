import signal
import os
import time
import urllib
import json

from simplejson import dumps as to_json
from simplejson import loads as from_json
from simplejson.scanner import JSONDecodeError

from webgui import start_gtk_thread
from webgui import launch_browser
from webgui import synchronous_gtk_message
from webgui import asynchronous_gtk_message
from webgui import kill_gtk_thread

from restapi import start_rest_api

class Global(object):
    quit = False
    @classmethod
    def set_quit(cls, *args, **kwargs):
        cls.quit = True


def main():

    rest_thread, rest_recv = start_rest_api()

    start_gtk_thread()

    # Create a proper file:// URL pointing to demo.xhtml:
    file = os.path.abspath('demo.xhtml')
    uri = 'file://' + urllib.pathname2url(file)
    browser, web_recv, web_send, window = \
        synchronous_gtk_message(launch_browser)(uri,
                                                quit_function=Global.set_quit,
                                                size=(480,320),
                                                fullscreen=True,
                                                echo=False
                                                )

    # Finally, here is our personalized main loop, 100% friendly
    # with "select" (although I am not using select here)!:
    last_second = time.time()
    uptime_seconds = 1
    clicks = 0
    while not Global.quit:

        current_time = time.time()
        again = False

        # Handle REST messages.
        msg = rest_recv()
        if msg:
            msg = from_json(msg)
            again = True

            if msg['action'] == "shutdown":
                shutdown()

            elif msg['action'] == "reload":
                browser.reload_bypass_cache()

            elif msg['action'] == "open":
                url = msg['data']
                browser.open(url)

            else:
                print "Unhandled REST action: %s" % msg['action']

        # Handle JS messages.
        msg = web_recv()
        if msg:
            try:
                msg = from_json(msg)
                again = True
            except JSONDecodeError as e:
                print "Error parsing message: '%s': %s" % (msg, str(e))

        if msg == "got-a-click":
            clicks += 1
            web_send('document.getElementById("messages").innerHTML = %s' %
                     to_json('%d clicks so far' % clicks))
            # If you are using jQuery, you can do this instead:
            # web_send('$("#messages").text(%s)' %
            #          to_json('%d clicks so far' % clicks))

        if msg == "reload-page":
            browser.reload_bypass_cache()

        if msg == "rest-message":
            print "REST: %s" % msg

        if current_time - last_second >= 1.0:
            web_send('document.getElementById("uptime-value").innerHTML = %s' %
                     to_json('%d' % uptime_seconds))
            # If you are using jQuery, you can do this instead:
            # web_send('$("#uptime-value").text(%s)'
            #        % to_json('%d' % uptime_seconds))
            uptime_seconds += 1
            last_second += 1.0


        if again: pass
        else:     time.sleep(0.1)

def shutdown():
    kill_gtk_thread()
    Global.set_quit()

def my_quit_wrapper(fun):
    signal.signal(signal.SIGINT, Global.set_quit)
    def fun2(*args, **kwargs):
        try:
            x = fun(*args, **kwargs) # equivalent to "apply"
        finally:
            shutdown()
        return x
    return fun2


if __name__ == '__main__': # <-- this line is optional
    my_quit_wrapper(main)()
