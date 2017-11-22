#!/usr/bin/python
# -*- coding: utf-8 -*-

from wiringpi import serialOpen, serialGetchar
from threading import Thread, Lock
from dzcom import DzSensor, PARAM_STRING_ELECTRIC_COUNTER, PARAM_STRING_CURRENT


class Teleinfo(Thread):
    """ Receives data from electric counter data using the teleinfo protocol
    and feeds Domoticz sensors.

    ERDF teleinfo protocol  is specified in the following dicument:
    http://www.magdiblog.fr/wp-content/uploads/2014/09/ERDF-NOI-CPT_02E.pdf

    Data from the electric counter are received on a serial link and are
    decoded in a background thread.

    Data are periodically transmitted to Domoticz sensors using DzSensor
    objects.

    Last received values can also be read with methods counter(), current() and
    power().

    A callback function can also be passed to the constructor, and will be
    automatically called in the background thread each time a current value is
    received.

    The background thread is started at creation of the Teleinfo object
    The stop() method can be used to terminate the background thread.
    """

    def __init__(self, device, dz_counter_idx=0, dz_current_idx=0,
                 update_period=20, callback=None):
        """Constructor

        Parameters:

        device: name of the serial port device used to receive the data.
            example: /dev/ttyAMA0

        dz_counter_idx (optionnal): index identifying a virtual counter
            in Domoticz where to send the counter base index (in Wh) and
            apparent power (in VA).

        dz_current_idx (optionnal): index identifying a virtual current
            sensor in Domoticz where to send the instantaneaous current values.
            (in Amps).

        update_period (optionnal) : period of time used to send the data to
            Domoticz.
            20 s by default.

        callback (optionnal): if present, this function will be called each
            time a currnt value is received. The current value is passed as
            parameter to the callback function.
            Note that the callback function shall be designed to not block or
            take a long time to execute.
        """

        Thread.__init__(self)
        self._callback = callback
        self.data_lock = Lock()     # lock for access to couter data

        # Create DzSensor objects if needed
        if dz_counter_idx:
            self.dz_counter = DzSensor(PARAM_STRING_ELECTRIC_COUNTER,
                                       dz_counter_idx, update_period)
        if dz_current_idx:
            self.dz_current = DzSensor(PARAM_STRING_CURRENT, dz_current_idx,
                                       update_period)

        # Open the COM port at 1200 bauds
        self.fd = serialOpen(device, 1200)
        self._current = -1
        self._power = -1
        self._index = -1
        self.start()

    def current(self):
        """Returns the last value of the instantaneaous current, in Amps"""
        with self.data_lock:
            iinst = self._current
        return iinst

    def power(self):
        """Returns the last value of the apparent power, in VA"""
        with self.data_lock:
            papp = self._power
        return papp

    def index(self):
        """Return the last  value of the base index, in Wh"""
        with self.data_lock:
            index = self._index
        return index

    def stop(self):
        """Stops the background task"""
        self._stop = True

    def run(self):
        """Backgroud task decoding the teleinfo frames.

        Do not call this method directly. It is called automatocally by
        the constructor.
        """

        def read_char(fd):
            # Reads chars from the serial device until the parity is correct.
            # Returns the first valid char received.
            while True:
                # read next byte
                b = serialGetchar(fd)
                if b >= 0:
                    # check even parity
                    p = True
                    m = 0x80
                    while m:
                        if (m & b):
                            p = not p
                        m = m >> 1
                    if p:
                        return chr(b & 0x7f)

        def read_word(fd):
            # Reads a space terminated sequence of char.
            # Returns the received word without the leading space
            word = ''
            c = read_char(fd)
            while c != ' ':
                word += c
                c = read_char(fd)
            return word

        def read_data(fd):
            # Reads a data line composed of a label and a value, terminated by
            # a checksum. Lines with wrong checksum are ignored.
            # Returns the labal and value from the first line received with a
            # alid checksum.
            while True:
                c = read_char(fd)
                while c != '\n':
                    c = read_char(fd)
                label = read_word(fd)
                value = read_word(fd)
                sum = ord(' ')
                for c in label:
                    sum += ord(c)
                for c in value:
                    sum += ord(c)
                sum = (sum & 0x3f) + 0x20
                c = read_char(fd)
                if sum == ord(c):
                    return label, value

        # Start od the background thread
        # negative value means not yet received.
        papp = -1
        base = -1
        iinst = -1
        self._stop = False
        # reception loop. A data (label, value) is received and processed at
        # each loop.
        while not self._stop:
            (label, value) = read_data(self.fd)
            if label == 'IINST':
                iinst = int(value)
                if self._callback:
                    self._callback(iinst)
                with self.data_lock:
                    self._current = iinst
                if self.dz_current:
                    self.dz_current.refresh(iinst)
            elif label == 'BASE':
                base = int(value)
                with self.data_lock:
                    self._index = base
                if self.dz_counter and papp >= 0:
                    self.dz_counter.refresh(papp, base)
            elif label == 'PAPP':
                papp = int(value)
                with self.data_lock:
                    self._power = int(value)
                if self.dz_counter and base >= 0:
                    self.dz_counter.refresh(papp, base)
        # stop() was invoked
        # We stop also sending cyclic updates to Domoticz sensors.
        if self.dz_current:
            self.dz_current.stop()
        if self.dz_counter:
            self.dz_counter.stop()
        return
