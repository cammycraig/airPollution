# Air Particulate Sensor Code
Open sourced software for monitoring PM2.5 and PM10 Air Particulate

![Image of Sensor](https://github.com/craigrc/airPollution/blob/main/Images/Air-Sensor-Image.PNG)

This project allows anyone to use an SDS011 air particulate sensor to monitor levels of PM2.5 & PM10 Air Particulate in order to view air quality in their local area.

## Read Air Particulate Values with Code

`matter.py`

airPolution/matter.py contains the code for monitoring air particulate values.
When ran, the file measures an average level of PM2.5 and PM10 in the air over a minute, in 15 minute intervals (1 on, 14 off) and writes these values to a **data.txt** file in the same directory. This code very heavily uses Github User [Zenfanja's](https://github.com/zefanja/) aqi.py as a base for the sensor code, and so all the credit goes to them for this!

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

## Set Up Individual Sensor with Server Host

### Method 1: Create System with Image (Recommended Option)

### Method 2: Create System from Scratch

## Set Up Coupled Node and Server

### Method 1: Create System with Image (Recommended Option)

- Download the two image files from <LOC>

- Image each onto a Pi

Set Up the Node

- Insert the SDS011 sensor into the node pi, connect it to a monitor, connect a keyboard and mouse, and plug in its sd card

- Power it

- Connect the Pi to your network

- Run 'ifconfig' and make a note of the IP for later

Set Up the Server

- Take your server Pi, connect it to a monitor, connect a keyboard and mouse, and plug in its sd card

- Connect your Pi to your wifi network

- Create an SSH key pair between the two Pis. A more detailed guide on doing this can be seen [here](https://debian-administration.org/article/530/SSH_with_authentication_key_instead_of_password).

  - Run 'ssh-keygen' and leave all fields default. 

  - Run 'ssh-copy-id -i .ssh/id_rsa.pub pi@<YOUR NODE PI IP>'

- Edit the index.py file in /var/www/cgi-bin and replace both the <NODE PI IP> references to the IP address of the Node Pi you set up.
    
- The website will be visible on the server pi at localhost/cgi-bin/ or on any device on your local network at <SERVER PI IP>/cgi-bin/

### Method 2: Create System from Scratch

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

- <SETUP PYTHON BASED WEB SERVER>
  
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

## To Come in a Future Update:

## Set Up Node Network of Sensors with Server Host

### Method 1: Create System with Image (Recommended Option)

#### Part 1: Server Pi

#### Part 2: Node Pis

### Method 2: Create System from Scratch

#### Part 1: Server Pi

#### Part 2: Node Pis
