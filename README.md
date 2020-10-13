# Air Particulate Sensor Code
Open sourced software for monitoring PM2.5 and PM10 Air Particulate

![Image of Sensor](https://github.com/craigrc/airPollution/blob/main/Images/Air-Sensor-Image.PNG)

This project allows anyone to use an SDS011 air particulate sensor to monitor levels of PM2.5 & PM10 Air Particulate in order to view air quality in their local area.

## Read Air Particulate Values with Code

`matter.py`

airPolution/matter.py contains the code for monitoring air particulate values.
When ran, the file measures an average level of PM2.5 and PM10 in the air over a minute, in 15 minute intervals (1 on, 14 off) and writes these values to a **data.txt** file in the same directory.

```python
Future: add <matter.py>
```

## Set Up Individual Sensor with Server Host

### Method 1: Create System with Image (Recommended Option)

### Method 2: Create System from Terminal

## Set Up Node Network of Sensors with Server Host

### Method 1: Create System with Image (Recommended Option)

#### Part 1: Server Pi

#### Part 2: Node Pi

### Method 2: Create System from Terminal

#### Part 1: Server Pi

#### Part 2: Node Pi
