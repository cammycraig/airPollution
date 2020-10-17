#!/usr/bin/env python

#Import Necessary Libraries
import pylab
import os
from datetime import datetime
from datetime import timedelta
import time

#Develop Content

#---Download file from other pi
os.system("scp pi@<NODE PI IP>:/home/pi/data.txt /var/www/cgi-bin")

#Read data from temp into file
datafile = open("./dataMaster.txt","r")
data = datafile.read()
datafile.close()
newdatafile = open("./data.txt","r")
lines = newdatafile.readlines()
newdatafile.close()
numLines = len(lines)
if numLines > 1:
    data += "\n"
    for lineNo in range(1,numLines):
        line = lines[lineNo]
        data += (line)
    datafile = open("./dataMaster.txt","w")
    datafile.write(data)
    newdatafile = open("./data.txt","w") 
    newdatafile.write("dateTime, PM2.5, PM10")
    datafile.close()
    newdatafile.close()
    #---Write newdatafile to other pi
    os.system("scp /var/www/cgi-bin/data.txt pi@<NODE PI IP>:/home/pi")
    

#Read data from master into file

class dateTimeLevel:
    def __init__(self, datetime, two, ten):
        self.datetime = datetime
        self.two = two
        self.ten = ten
        
class dateAverageLevel:
    def __init__(self, date, two, ten):
        self.date = date
        self.two = two
        self.ten = ten
        
dateTimeLevels = []
dateAverageLevels = []

datafile = open("./dataMaster.txt","r")
lines = datafile.readlines()
datafile.close()
numLines = len(lines)
if numLines > 1:
    for lineNo in range(1,numLines):
        line = lines[lineNo]
        line = line.strip()
        lineData = line.split(", ")
        level = dateTimeLevel(lineData[0],lineData[1],lineData[2])
        dateTimeLevels.append(level)

inDate = ((dateTimeLevels[0]).datetime)[0:10]
n = 0
twosum = 0
tensum = 0
for item in dateTimeLevels:
    if (item.datetime)[0:10] == inDate:
        twosum += float(item.two)
        tensum += float(item.ten)
        n += 1
    else:
        twoavg = round((twosum/n),2)
        tenavg = round((tensum/n),2)
        level = dateAverageLevel(inDate,str(twoavg),str(tenavg))
        dateAverageLevels.append(level)
        n = 1
        twosum = float(item.two)
        tensum = float(item.ten)
        inDate = (item.datetime)[0:10]
twoavg = round((twosum/n),2)
tenavg = round((tensum/n),2)
level = dateAverageLevel(inDate,str(twoavg),str(tenavg))
dateAverageLevels.append(level)

######Generate 24.png#####
numArray = []
twoArray = []
tenArray = []
displayDateTime = []

#Find 24 hours before
lastEntry = dateTimeLevels[-1]
lastDateTime = lastEntry.datetime
dateObject = datetime.strptime(lastDateTime, "%d.%m.%Y %H:%M")
lowerTime = (dateObject - timedelta(hours=24)).strftime("%d.%m.%Y %H:%M")

#Generate data arrays
for dateTimeLevel in dateTimeLevels:
    dateTime = dateTimeLevel.datetime
    if dateTime > lowerTime:
        twoArray.append(float(dateTimeLevel.two))
        tenArray.append(float(dateTimeLevel.ten))
        displayDateTime.append(dateTime)

if len(displayDateTime) > 3:
    dates = [""]*(len(displayDateTime)-2)
    dates.insert(0, displayDateTime[0])
    dates.append(displayDateTime[-1])
    displayDateTime = dates
    
#Generate numArray
for num in range(1, (len(displayDateTime))+1):
    numArray.append(num)

#Draw graph
pylab.plot(numArray,twoArray,label=("PM2.5"))
pylab.plot(numArray,tenArray,label=("PM10"))
pylab.xticks(numArray,displayDateTime)
pylab.title("PM2.5 and PM10 Levels in the Last 24 Hours")
pylab.xlabel("Date/Time")
pylab.ylabel("Level")
pylab.legend(loc='upper left')
filename = ("./media/24.png")
pylab.savefig(filename)
pylab.close()

######Generate 7.png#####
numArray = []
twoArray = []
tenArray = []
displayDateTime = []

#Find 7 days before
lastEntry = dateAverageLevels[-1]
lastDateTime = lastEntry.date
dateObject = datetime.strptime(lastDateTime, "%d.%m.%Y")
lowerTime = (dateObject - timedelta(days=7)).strftime("%d.%m.%Y")

#Generate data arrays
for dateTimeLevel in dateAverageLevels:
    dateTime = dateTimeLevel.date
    if dateTime > lowerTime:
        twoArray.append(float(dateTimeLevel.two))
        tenArray.append(float(dateTimeLevel.ten))
        displayDateTime.append(dateTime)

if len(displayDateTime) > 3:
    dates = [""]*(len(displayDateTime)-2)
    dates.insert(0, displayDateTime[0])
    dates.append(displayDateTime[-1])
    displayDateTime = dates

#Generate numArray
for num in range(1, (len(displayDateTime))+1):
    numArray.append(num)

#Draw graph
pylab.plot(numArray,twoArray,label=("PM2.5"))
pylab.plot(numArray,tenArray,label=("PM10"))
pylab.xticks(numArray,displayDateTime)
pylab.title("PM2.5 and PM10 Levels in the Last 7 Days")
pylab.xlabel("Date")
pylab.ylabel("Level")
pylab.legend(loc='upper left')
filename = ("./media/7.png")
pylab.savefig(filename)
pylab.close()

######Generate all.png#####
numArray = []
twoArray = []
tenArray = []
displayDateTime = []

#Generate data arrays
for dateTimeLevel in dateAverageLevels:
    dateTime = dateTimeLevel.date
    twoArray.append(float(dateTimeLevel.two))
    tenArray.append(float(dateTimeLevel.ten))
    displayDateTime.append(dateTime)

if len(displayDateTime) > 3:
    dates = [""]*(len(displayDateTime)-2)
    dates.insert(0, displayDateTime[0])
    dates.append(displayDateTime[-1])
    displayDateTime = dates

#Generate numArray
for num in range(1, (len(displayDateTime))+1):
    numArray.append(num)

#Draw graph
pylab.plot(numArray,twoArray,label=("PM2.5"))
pylab.plot(numArray,tenArray,label=("PM10"))
pylab.xticks(numArray,displayDateTime)
pylab.title("PM2.5 and PM10 Levels Over All Time")
pylab.xlabel("Date")
pylab.ylabel("Level")
pylab.legend(loc='upper left')
filename = ("./media/all.png")
pylab.savefig(filename)
pylab.close()

#Generate Page
print("<html>")
print("<head>")
print("<link rel='icon' href='./media/logo.png'>")
print("<title>Air Particulate Levels</title>")
print("<link rel='stylesheet' href='./css/mycss.css'>")
print("</head>")
print("<body>")
print("<div>")
print("<h1>AIR PARTICULATE LEVELS</h1>")
print("<br>")
print("<p>Here the values for the sensor are displayed. Read more at <a href='https://github.com/craigrc/airPollution'>my github</a>.</p>")
print("<br>")
print("<h2>Data</h2>")
print("<br>")
print("<table>")
print("<tr>")
print("<th>dateTime</th>")
print("<th>PM2.5</th>")
print("<th>PM10</th>")
print("</tr>")
for entry in dateTimeLevels:
    print("<tr>")
    print("<td>"+entry.datetime+"</th>")
    print("<td>"+entry.two+"</th>")
    print("<td>"+entry.ten+"</th>")
    print("</tr>")
print("</table>")
print("<br>")
print("<h2>Graph of the Past 24 Hours</h2>")
print("<br>")
print("<img src='./media/24.png'>")
print("<br>")
print("<h2>Graph of the Past 7 Days</h2>")
print("<br>")
print("<img src='./media/7.png'>")
print("<br>")
print("<h2>Graph of All Time Data</h2>")
print("<br>")
print("<img src='./media/all.png'>")
print("</div>")
print("</body>")
print("</html>")
