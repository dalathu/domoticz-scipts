#!/usr/bin/python
# -*- coding: latin-1 -*-
# import urllib
from requests import get
from time import time
from threading import Thread, Lock, Timer
from collections import deque


# parameter strings to be used for the different kind of sensors
PARAM_STRING_SWITCH = \
    '?type=command&param=switchlight&idx=IDX&switchcmd=%s'
PARAM_STRING_SELECTOR_SWITCH = \
    '?type=command&param=switchlight&idx=IDX&switchcmd=Set Level&level=%s'
PARAM_STRING_CURRENT = \
    '?type=command&param=udevice&idx=IDX&nvalue=0&svalue=%s'
PARAM_STRING_ELECTRIC_COUNTER = \
    '?type=command&param=udevice&idx=IDX&nvalue=0&svalue=%s;%s'
PARAM_STRING_TEXT = \
    '?type=command&param=udevice&idx=IDX&nvalue=0&svalue=%s'

BASE_URL = 'http://127.0.0.1:8080/json.htm'

PARAM_LOG = '?type=command&param=addlogmessage&message=%s'


def open_url(url):
    try:
        # print 'GET URL :'+url
        # reponse = urllib.urlopen(url).read()
        get(url)
        # print reponse
        return True
    except IOError:
        print 'erreur communication Domoticz'
        return False


def getStatus(idx):
    url = BASE_URL + '?type=devices&rid=%s' % idx
    r = get(url)
    data = r.json()
    if data['result'][0]['SubType'] == 'Switch':
        return (data['result'][0]['Status'] == 'On')
    elif data['result'][0]['SubType'] == 'Selector Switch':
        return data['result'][0]['Level']
    else:
        return 0


class DzSensor:
    """Class used to update a Domoticz sensor using the HTTP API
    """

    LOOP_TIME = 10

    def __init__(self, param_string, idx, t_min=5, t_max=0):
        """Create a DzSensor object
        Parameters:
        - param_string: parameter string to be used in the URL.
          Use predefined PARAM_STRING_xxx.
        - idx: index of the domoticz device
        - t_min: minimum transmission period:
          Updates occurring within t_min from the last tranasmission are
          ignored
        - t_max: maximum transmission period:
          A new transmission occurs t_max after the last transmission, in
          absence of refresh command.
          t_max = 0 is the default value and means that no retransmission will
          occur in absence of refresh
          command.
        """
        self.idx = idx
        self.t_min = t_min
        self.t_max = t_max
        self.url = BASE_URL + param_string.replace('IDX', str(idx))
        self.values = None
        self.last_sent = 0
        self.lock = Lock()
        self.timer = None
        return

    def stop(self):
        if self.timer:
            self.timer.cancel()
        return

    def _send(self):
        # print 'transmission', self.values
        with self.lock:
            url = self.url % self.values
        if open_url(url):
            self.last_sent = time()
            if self.t_max:
                self.timer = Timer(self.t_max, self._send)
                self.timer.start()

    def refresh(self, *values):
        # print 'refresh', values
        if cmp(values, self.values) != 0:
            with self.lock:
                self.values = values
                wait_time = max(0, self.last_sent + self.t_min - time())
                if self.timer:
                    self.timer.cancel()
                self.timer = Timer(wait_time, self._send)
                self.timer.start()

    def send(self, *values):
        # print 'send', values
        with self.lock:
            self.values = values
            wait_time = max(0, self.last_sent + self.t_min - time())
            if self.timer:
                self.timer.cancel()
            self.timer = Timer(wait_time, self._send)
            self.timer.start()


class DzLog:
    """Class used to send messages to the Domoticz log
    """

    def __init__(self):
        """Create a DzLog object
        """
        self.message_queue = deque()
        return

    def send(self, message):
        self.message_queue.append(message)
        t = Thread(target=self._transmit)
        t.start()
        return

    def _transmit(self):
        while len(self.message_queue):
            message = self.message_queue.popleft()
            url = BASE_URL + PARAM_LOG % (message)
            open_url(url)
        return
