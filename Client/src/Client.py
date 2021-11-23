# Adapted from Practical 4 code submission so as incorporate communication with server raspberry pi.
import sys
# Importing of relevant libraries
import datetime
import socket
import time
import threading
import RPi.GPIO as GPIO
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# initialise global delay variable.
delay = 10  # default run time delay
dataTransmissionFlag = False # flag to determine whether we are sending data or not.
clientSocket = None
BUFFER_SIZE = 2048


# code for practical 4.
# method for button press
def btn_pressed(channel):
    global delay

    if delay == 10:
        delay = 5
    elif delay == 5:
        delay = 1
    elif delay == 1:
        delay = 10


# initialise GPIO
def setupGPIO():
        # create the spi bus
    global spi
    spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

    # create the cs (chip select)
    global cs
    cs = digitalio.DigitalInOut(board.D5)

    # create the mcp object
    global mcp
    mcp = MCP.MCP3008(spi, cs)

    try:
        # set button for input
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # setup debouncing and callbacks
        GPIO.add_event_detect(21, GPIO.FALLING, callback=btn_pressed, bouncetime=200)

    except KeyboardInterrupt:  # IF CTRL+C is pressed exit cleanly
        print("Keyboard interrupt")




# method to read temperature from sensor
def getTemperature():
    global temp
    global tempV
    t = AnalogIn(mcp, MCP.P1)
    temp = t.value
    tempV = t.voltage
    return temp,tempV
    


# method to read light off sensor
def getLight():
    global light
    l = AnalogIn(mcp, MCP.P2)
    light = l.value
    return light


# connection for tcp connection
def formConnection():
    socketConnRes = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketConnRes.connect(('172.20.10.4', 1234))
    print("Connection formed")
    return socketConnRes


# Responsible for receiving commands from the server
def transmissionSetter():
    global dataTransmissionFlag
    while True:
        transmittedData = clientSocket.recv(BUFFER_SIZE).decode()
        if transmittedData == 'Activate': #turn on sensors
            dataTransmissionFlag = True
            clientSocket.send('ACK'.encode())

        elif transmittedData == 'Deactivate':# turn off sensors
            dataTransmissionFlag = False
            clientSocket.send('ACK'.encode())

        elif transmittedData == 'Exit':# exit process
            sys.exit()

        elif transmittedData == 'Check Status':# check status
            dataTransmissionFlag = False
            clientSocket.send('ON'.encode())
            time.sleep(delay)             
            dataTransmissionFlag = True

        elif transmittedData == 'DownloadLog':#download log
            dataTransmissionFlag = True
            clientSocket.send('DownloadLog'.encode())

        elif transmittedData=='CheckLog':#check log
            dataTransmissionFlag = True
            clientSocket.send('CheckLog'.encode())



if __name__ == '__main__':
    setupGPIO()
    t = 0
    clientSocket = formConnection()  # setup the connection with the server.
    receptionThread = threading.Thread(target=transmissionSetter, args=())  # setup thread to handle reception of packets incoming from server.
    receptionThread.start()

    while True:

        while dataTransmissionFlag:  # loop continuously while server indicates need for readings.
          
            # tempThread = threading.Thread(target=getTemperature)
            # lightThread = threading.Thread(target=getLight)
            # tempThread.start()
            # lightThread.start()
            # tempThread.join()
            # lightThread.join()

            temp,voltage=getTemperature()
            tempCon = round((voltage - 0.5)/0.01)
            light=getLight()

            # data collected from sensors.
            messageToSend =  str(light) + " " + str(temp) + " "+ str(tempCon)
           
            # time at which reading was made.
            readingTime = str(datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S"))
            completeMessage = readingTime + " " + messageToSend
            print(completeMessage)
            clientSocket.send(completeMessage.encode())
            t += delay
            time.sleep(delay)
