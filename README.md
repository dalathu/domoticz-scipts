# domoticz-scipts
Here I'm sharing some of my home automation scripts for Domoticz running on a Raspberry Pi. They are written in python and lua.

## python scripts

### dzcom.py
This package provides some classes and functions to communicate with Domoticz using its [JSON API URL][1].

By default the base URL used is `http://127.0.0.1:8080/json.htm`. This can be modified if you need to communicate with a distant Domoticz server, by changing the `BASE_URL` string. This change shall be performed before creating DzSensor objects.

#### function getStatus(idx)
Reads and returns the status of the Domoticz sensor with ID number idx.
Only *Switch* and *Selector Switch* sensor types are supported.

#### class DzSensor

DzSensor objects are coupled to a Domoticz virtual sensor and are used to update the value of the Domoticz sensor.

##### Usage:
DzSensor creation:
```
sensor = DzSensor(param_string, idx, t_min, t_max)
```

*param_string*: Constant string depending on the type of sensor in Domoticz. Use the following pre-defined param strings:  
* `PARAM_STRING_SWITCH`
* `PARAM_STRING_SELECTOR_SWITCH`
* `PARAM_STRING_CURRENT`
* `PARAM_STRING_ELECTRIC_COUNTER`
* `PARAM_STRING_TEXT`

*idx*: identifier number of the Domoticz virtual sensor that will be coupled with this DzSensor object.

*t_min* (optional): minimum transmission period. Updates occurring within t_min from the last transmission are ignored. This parameter is optional with 5 s as default value. This is to avoid loading too much Domoticz.

*t_max* (optional): maximum transmission period. A new transmission will occur t_max after the last transmission in absence of call to the `send` or `refresh` methods. If this parameter is ommited, there is no periodic transmission in absence of call to the `send` or `refresh` methods. Periodic transmission is usually needed so that Domoticz does not detect a timeout on the sensor.

Sending value(s) to the Domoticz sensor:
```
sensor.send(value...)
```

*value...*: value(s) to be transmitted to the Domoticz sensor. The number of values depends on the sensor type. Some sensor type like counters require more than one value.  The actual number of values explected can be known by counting the `%s` in the `param_string`.  
This method returns immediately and the actual transmisson is performed in a background thread.

Refreshing values(s) of the Domoticz sensor:
```
sensor.refresh(value...)
```

The `refresh` method does the same as the `send` method except that no transmission occurs if the value(s) is(are) the same as the previous value(s). This shall be prefered to the `send` method in order to minimize communication in case the sensor data source is faster than required in Domoticz.

#### class DzLog

A DzLog object is used to send messages to the Domoticz log.

##### Usage:
DzLog creation:
```
dz_log = DzLog()
```

Sending a string to the Domoticz log:
```
dz_log.send("This will be written in the Domoticz log.")
```

The send method puts the message in a queue and returns immediatly. The message queue is proccessed in a background thread.

### teleinfo.py
This package provides a class that reads the information transmitted by an electric counter using the *teleinfo* protocol.  
The *teleinfo* protocol is used on french electric couters. It's specification can be found in [this document][2].

## lua scripts
Coming soon...

[1]: https://www.domoticz.com/wiki/Domoticz_API/JSON_URL%27s
[2]: http://www.magdiblog.fr/wp-content/uploads/2014/09/ERDF-NOI-CPT_02E.pdf
