# Air Particulate Sensor Code
Open sourced software for monitoring PM2.5 and PM10 Air Particulate

![Image of Sensor](https://github.com/craigrc/airPollution/blob/main/Images/Air-Sensor-Image.PNG)

This project allows anyone to use an SDS011 air particulate sensor to monitor levels of PM2.5 & PM10 Air Particulate in order to view air quality in their local area.
This project can also couple really well with a 3D printed case for the sensor if you want to attach it somewhere permanently, such as Thingiverse User [Piersoft's](https://www.thingiverse.com/piersoft/designs) "SDS011 Stevenson Case with NodeMCU".
To create a system choose one and follow its respective instructions.
There are now two different versions of this project that you can use:

- Online Version / beansticks.cf: This new site allows for users to create accounts and manage multiple node networks, displaying data in much greater detail than the latter version, as well as being far more robust. 

- Local Version: If you would prefer to have the entire project running locally on your network - if you have concerns for privacy or if you have an unstable internet connection, for example - then the latter version would probably better suit you. Note that this means your system will not have access to the advanced features and more stable validation as well as improved UI seen in the former. This system version is also unfortunately now depricated and these changes will not be coming. Also note that the setup for this system is far more expensive and dificult and is thus no longer recommended.

  - This will produce a site hosted on your local network where you can view and visualise levels in real-time. <A build of what this will roughly look like can be seen [here](http://craigrc.gq/pollutionWebsiteExample/index.html). Note how in this demonstration values were only recorded over one day and as such the 7 day and all time graphs cannot be made without a larger dataset.
  
## Online Version / beansticks.cf

### Read Air Particulate Values with Code

`readAirPollution.py`

airPolution/readAirPollution.py contains the code for monitoring air particulate values for an Online System.
When ran, the file measures an average level of PM2.5 and PM10 in the air over a minute, in 15 minute intervals (1 on, 14 off) and writes these values to a **data.txt** file in the same directory, and submits these values to database on beansticks.cf. This code very heavily uses Github User [Zenfanja's](https://github.com/zefanja/) aqi.py as a base for the sensor code, and so all the credit goes to them for that!

```python
from __future__ import print_function
import serial, struct, sys, time, json, subprocess
import requests
from datetime import datetime
from datetime import timedelta
import time

DEBUG = 0
CMD_MODE = 2
CMD_QUERY_DATA = 4
CMD_DEVICE_ID = 5
CMD_SLEEP = 6
CMD_FIRMWARE = 7
CMD_WORKING_PERIOD = 8
MODE_ACTIVE = 0
MODE_QUERY = 1
PERIOD_CONTINUOUS = 0

JSON_FILE = '/var/www/html/aqi.json'

MQTT_HOST = ''
MQTT_TOPIC = '/weather/particulatematter'

ser = serial.Serial()
ser.port = "/dev/ttyUSB0"
ser.baudrate = 9600

ser.open()
ser.flushInput()

byte, data = 0, ""


def dump(d, prefix=''):
    print(prefix + ' '.join(x.encode('hex') for x in d))


def construct_command(cmd, data=[]):
    assert len(data) <= 12
    data += [0, ] * (12 - len(data))
    checksum = (sum(data) + cmd - 2) % 256
    ret = "\xaa\xb4" + chr(cmd)
    ret += ''.join(chr(x) for x in data)
    ret += "\xff\xff" + chr(checksum) + "\xab"

    if DEBUG:
        dump(ret, '> ')
    return ret


def process_data(d):
    r = struct.unpack('<HHxxBB', d[2:])
    pm25 = r[0] / 10.0
    pm10 = r[1] / 10.0
    checksum = sum(ord(v) for v in d[2:8]) % 256
    return [pm25, pm10]

def process_version(d):
    r = struct.unpack('<BBBHBB', d[3:])
    checksum = sum(ord(v) for v in d[2:8]) % 256
    print("Y: {}, M: {}, D: {}, ID: {}, CRC={}".format(r[0], r[1], r[2], hex(r[3]),
                                                       "OK" if (checksum == r[4] and r[5] == 0xab) else "NOK"))


def read_response():
    byte = 0
    while byte != "\xaa":
        byte = ser.read(size=1)

    d = ser.read(size=9)

    if DEBUG:
        dump(d, '< ')
    return byte + d


def cmd_set_mode(mode=MODE_QUERY):
    ser.write(construct_command(CMD_MODE, [0x1, mode]))
    read_response()


def cmd_query_data():
    ser.write(construct_command(CMD_QUERY_DATA))
    d = read_response()
    values = []
    if d[1] == "\xc0":
        values = process_data(d)
    return values


def cmd_set_sleep(sleep):
    mode = 0 if sleep else 1
    ser.write(construct_command(CMD_SLEEP, [0x1, mode]))
    read_response()


def cmd_set_working_period(period):
    ser.write(construct_command(CMD_WORKING_PERIOD, [0x1, period]))
    read_response()


def cmd_firmware_ver():
    ser.write(construct_command(CMD_FIRMWARE))
    d = read_response()
    process_version(d)


def cmd_set_id(id):
    id_h = (id >> 8) % 256
    id_l = id % 256
    ser.write(construct_command(CMD_DEVICE_ID, [0] * 10 + [id_l, id_h]))
    read_response()


def pub_mqtt(jsonrow):
    cmd = ['mosquitto_pub', '-h', MQTT_HOST, '-t', MQTT_TOPIC, '-s']
    print('Publishing using:', cmd)
    with subprocess.Popen(cmd, shell=False, bufsize=0, stdin=subprocess.PIPE).stdin as f:
        json.dump(jsonrow, f)

url = 'https://beansticks.cf/uploadData.php'

if __name__ == "__main__":
    cmd_set_sleep(0)
    cmd_firmware_ver()
    cmd_set_working_period(PERIOD_CONTINUOUS)
    cmd_set_mode(MODE_QUERY);
    while True:
        cmd_set_sleep(0)
        pm2T = 0
        pm10T = 0
        for t in range(30):
            values = cmd_query_data();
            if values is not None and len(values) == 2:
                print("PM2.5: ", values[0], ", PM10: ", values[1])
                pm2T += values[0]
                pm10T += values[1]
                time.sleep(2)
        pm2TAvg = pm2T / 30
        pm10TAvg = pm10T / 30
        dtime = time.strftime("%d.%m.%Y %H:%M")
        dtime = str(dtime)
        content = "\n" + dtime + ", " + str(round(pm2TAvg,2)) + ", " + str(round(pm10TAvg,2))
        datafile = open("./data.txt", "a")
        datafile.write(content)
        datafile.close()
        day0 = "1.10.2020 00:00"
        dateObject = datetime.strptime(dtime, "%d.%m.%Y %H:%M")
        day0object = datetime.strptime(day0, "%d.%m.%Y %H:%M")
        d0_ts = time.mktime(day0object.timetuple())
        dt_ts = time.mktime(dateObject.timetuple())
        timeID = (int((dt_ts-d0_ts) / 900))
        myobj = {'submitID': 'b89455a', 'timeID': str(timeID), 'pm25': str(pm2TAvg), 'pm10': str(pm10TAvg), 'datetime': dtime}
        x = requests.post(url, data = myobj)
        cmd_set_sleep(14)
        time.sleep((60*14))
```

### Setup for an Online System

You will need only at least one Raspberry Pi for this system, however the instructions can be followed as many times as you want to configure a number of nodes to form a network.

Configuring your beansticks.cf Account:

- Firstly, go to [beansticks.cf](https://beansticks.cf/) and navigate to **Upload Data**. 

- Here you can firstly **Create a New Network** which will also take you through the process of registering an account on the website.

- When this is done, you can return to **Upload Data** and **Create a New Node** to register a new Node in the Network you have just created. This will give you a 'submitID' which you should make a note of, but will also always be visible in **My Data**.

Configuring the Node Pi:

- Firstly, create a fresh boot of Raspbian desktop on your Pi.

- Connect the pi to your internet

- In the console, type 'sudo raspi-config'

  - Configure the Pi to boot with desktop auto-login if this has not already been done

- Run 'sudo apt install git-core python-serial python-enum'

- Install the readAirPollution.py file onto /home/pi 

  - This can be easily done with SFTP, a USB or even downloading directly from this Github over the internet
  
  - Line 153 must be edited from...
 
`myobj = {'submitID': 'submitID', 'timeID': str(timeID), 'pm25': str(pm2TAvg), 'pm10': str(pm10TAvg), 'datetime': dtime}`

  - ...to reflect your submitID you noted earlier

- Create a data.txt file using 'sudo nano data.txt'

  - In this file, type:

`dateTime, PM2.5, PM10`

  - then save the file.
  
- Next, we are going to automate running this file on startup:

  - First, type 'sudo crontab -e' then - at the bottom of the file - add the line

`@reboot cd /home/pi && python ./readAirPollution.py`

- Now, 'sudo halt' the Pi, and place it wherever you wish to record data (within the reach of your wifi network!) and when you next power it, it will be fully functional!

Finally, your Node's data will be visible at https://beansticks.cf/node.php?name=NodeName where NodeName is the name you chose earlier

## Local Version

### Read Air Particulate Values with Code

`matter.py`

airPolution/matter.py contains the code for monitoring air particulate values.
When ran, the file measures an average level of PM2.5 and PM10 in the air over a minute, in 15 minute intervals (1 on, 14 off) and writes these values to a **data.txt** file in the same directory. This code very heavily uses Github User [Zenfanja's](https://github.com/zefanja/) aqi.py as a base for the sensor code, and so all the credit goes to them for that!

```python
from __future__ import print_function
import serial, struct, sys, time, json, subprocess

DEBUG = 0
CMD_MODE = 2
CMD_QUERY_DATA = 4
CMD_DEVICE_ID = 5
CMD_SLEEP = 6
CMD_FIRMWARE = 7
CMD_WORKING_PERIOD = 8
MODE_ACTIVE = 0
MODE_QUERY = 1
PERIOD_CONTINUOUS = 0

JSON_FILE = '/var/www/html/aqi.json'

MQTT_HOST = ''
MQTT_TOPIC = '/weather/particulatematter'

ser = serial.Serial()
ser.port = "/dev/ttyUSB0"
ser.baudrate = 9600

ser.open()
ser.flushInput()

byte, data = 0, ""


def dump(d, prefix=''):
    print(prefix + ' '.join(x.encode('hex') for x in d))


def construct_command(cmd, data=[]):
    assert len(data) <= 12
    data += [0, ] * (12 - len(data))
    checksum = (sum(data) + cmd - 2) % 256
    ret = "\xaa\xb4" + chr(cmd)
    ret += ''.join(chr(x) for x in data)
    ret += "\xff\xff" + chr(checksum) + "\xab"

    if DEBUG:
        dump(ret, '> ')
    return ret


def process_data(d):
    r = struct.unpack('<HHxxBB', d[2:])
    pm25 = r[0] / 10.0
    pm10 = r[1] / 10.0
    checksum = sum(ord(v) for v in d[2:8]) % 256
    return [pm25, pm10]

def process_version(d):
    r = struct.unpack('<BBBHBB', d[3:])
    checksum = sum(ord(v) for v in d[2:8]) % 256
    print("Y: {}, M: {}, D: {}, ID: {}, CRC={}".format(r[0], r[1], r[2], hex(r[3]),
                                                       "OK" if (checksum == r[4] and r[5] == 0xab) else "NOK"))


def read_response():
    byte = 0
    while byte != "\xaa":
        byte = ser.read(size=1)

    d = ser.read(size=9)

    if DEBUG:
        dump(d, '< ')
    return byte + d


def cmd_set_mode(mode=MODE_QUERY):
    ser.write(construct_command(CMD_MODE, [0x1, mode]))
    read_response()


def cmd_query_data():
    ser.write(construct_command(CMD_QUERY_DATA))
    d = read_response()
    values = []
    if d[1] == "\xc0":
        values = process_data(d)
    return values


def cmd_set_sleep(sleep):
    mode = 0 if sleep else 1
    ser.write(construct_command(CMD_SLEEP, [0x1, mode]))
    read_response()


def cmd_set_working_period(period):
    ser.write(construct_command(CMD_WORKING_PERIOD, [0x1, period]))
    read_response()


def cmd_firmware_ver():
    ser.write(construct_command(CMD_FIRMWARE))
    d = read_response()
    process_version(d)


def cmd_set_id(id):
    id_h = (id >> 8) % 256
    id_l = id % 256
    ser.write(construct_command(CMD_DEVICE_ID, [0] * 10 + [id_l, id_h]))
    read_response()


def pub_mqtt(jsonrow):
    cmd = ['mosquitto_pub', '-h', MQTT_HOST, '-t', MQTT_TOPIC, '-s']
    print('Publishing using:', cmd)
    with subprocess.Popen(cmd, shell=False, bufsize=0, stdin=subprocess.PIPE).stdin as f:
        json.dump(jsonrow, f)


if __name__ == "__main__":
    cmd_set_sleep(0)
    cmd_firmware_ver()
    cmd_set_working_period(PERIOD_CONTINUOUS)
    cmd_set_mode(MODE_QUERY);
    while True:
        cmd_set_sleep(0)
        pm2T = 0
        pm10T = 0
        for t in range(30):
            values = cmd_query_data();
            if values is not None and len(values) == 2:
                print("PM2.5: ", values[0], ", PM10: ", values[1])
                pm2T += values[0]
                pm10T += values[1]
                time.sleep(2)
        pm2TAvg = pm2T / 30
        pm10TAvg = pm10T / 30
        dtime = time.strftime("%d.%m.%Y %H:%M")
        content = "\n" + str(dtime) + ", " + str(round(pm2TAvg,2)) + ", " + str(round(pm10TAvg,2))
        datafile = open("./data.txt", "a")
        datafile.write(content)
        datafile.close()

        cmd_set_sleep(14)
        time.sleep((60*14))
```

### Setup for a Local System

You will need two Raspberry Pi's - one as a Server Pi and one as a Node Pi - and an SDS011 sensor.

On the Sensor Pi:

- Set up a fresh boot of raspbian with desktop

- Connect the pi to your internet

- In the console, type 'sudo raspi-config'

  - Here, enable SSH
  
  - And configure the Pi to boot with desktop auto-login
 
- Run 'ifconfig' to find the IP address of this Pi (make sure to make a note of this for later!)

- Run 'sudo apt install git-core python-serial python-enum'

- Install the matter.py file onto /home/pi 

  - This can be easily done with SFTP, a USB or even downloading directly from this Github over the internet

- Create a data.txt file using 'sudo nano data.txt'

  - In this file, type:

`dateTime, PM2.5, PM10`

  - then save the file.
  
- Next, we are going to automate running this file on startup:

  - First, type 'sudo crontab -e' then - at the bottom of the file - add the line

`@reboot cd /home/pi && python ./matter.py`

Now, 'sudo halt' the Pi, and place it wherever you wish to record data (within the reach of your wifi network!) and when you next power it, it will be fully functional!

On the Server Pi:

- Set up a fresh boot of raspbian with desktop

- Configure a 'lighttpd' Python based web server
  
- Connect the pi to your wifi

- Enable SSH on this pi too.

- Run 'ifconfig' and make a note of the server pi IP.

- Create an SSH key pair between the two Pis. A more detailed guide on doing this can be seen [here](https://debian-administration.org/article/530/SSH_with_authentication_key_instead_of_password).

  - Run 'ssh-keygen' and leave all fields default. 

  - Run 'ssh-copy-id -i .ssh/id_rsa.pub pi@<YOUR NODE PI IP>'
  
- Install the server files

  - Install all the files from airPollution/cgi-bin into /var/www/cgi-bin
  
  - In the command line, navigate to /var/www and run 'sudo chmod -R 777 ./cgi-bin/
  
  - Edit the new index.py file and replace both the <NODE PI IP> references to the IP address of the Node Pi you set up.

Finally, the website will be visible on the server pi at localhost/cgi-bin/ or on any device on your local network at <SERVER PI IP>/cgi-bin/

#### FAQ

- Q: My system has stopped working. Why?

  - A: Since this setup uses static IP's, if your system has suddenly stopped recording values, one or more of the IP's have probably changed. Contact your network administrator for help setting up a static IP, or if you are doing this on your home system, look up how to do this on your broadband. This is quite rare however and is something that should not have too large an impact on the performance of your system in general.
