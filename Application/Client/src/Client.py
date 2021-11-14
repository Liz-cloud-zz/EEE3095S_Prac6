#Adapted from Practical 4 code submission so as incorperate communication with server raspberry pi.

#Importing of relevant libraries
from datetime import datetime
from socket import socket
import time
import threading
import RPi.GPIO as GPIO
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

#initialise global delay variable.
delay = 10

#initialise global tcp variables
dataTransmissionFlag = True  # flag to determine whether we are sending data or not.
clientSocket = None

#code for practical 4.
#method for button press
def btn_pressed(channel):
    global delay

    if delay == 10:
        delay = 5 
    elif delay == 5:
        delay = 1
    elif delay == 1:
        delay = 10

#initialise GPIO    
def setupGPIO():
    try:
        #set button for input
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(21, GPIO.IN, pull_up_DOWN=GPIO.PUD_UP)

        #setup debouncing and callbacks
        GPIO.add_event_detect(21, GPIO.FALLING, callback=btn_pressed, bouncetime=200)

    except KeyboardInterrupt: #IF CTRL+C is pressed exit cleanly
        print("Keyboard interrupt")

    #create the spi bus
    global spi
    spi = busio.SPI(clock=board.SCK, MISO=board.MISO,MOSI=board.MOSI)

    #create the cs (chip select)
    global cs
    cs = digitalio.DigitalInOut(board.D5)

    #create the mcp object
    global mcp
    mcp = MCP.MCP3008(spi, cs)

    #method to read temperature from sensor
    def getTemperature():
        global temp
        global tempV
        t = AnalogIn(mcp, MCP.P1)
        temp = t.value
        tempV = t.voltage

    #method to read light off sensor
    def getLight():
        global light
        l = AnalogIn(mcp, MCP.P2)
        light = l.value


    #connection for tcp connection
    def formConnection():
        socketConnRes = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socketConnRes.connect(('192.168.43.68',1234))
        return socketConnRes

    def transmissionSetter():
        global dataTransmissionFlag
        while(True):
            transmittedData = clientSocket.recv(BUFFER_SIZE).decode()
            if transmittedData == "Collect":
                #acknowledgement
                dataTransmissionFlag = True
            elif transmittedData == "Cease":
                #acknowledgement
                dataTransmissionFlag = False

    if __name__ == '__main__':
        setupGPIO()
        t = 0
        clientSocket = formConnection()  # setup the connection with the server.
        receptionThread = threading.Thread(target=transmissionSetter,args=())  # setup thread to handle reception of packets incoming from server.
        receptionThread.start()

        while(True):
            while(dataTransmissionFlag): # loop continously while server indicates need for readings.
                tempThread = threading.Thread(target=getTemperature)
                lightThread = threading.Thread(target=getLight)

                tempThread.start()
                lightThread.start()

                tempThread.join()
                lightThread.join()

                voltage = temp * (5/1023)
                tempCon = round((voltage-0.5),2)

                #data collected from sensors.
                messageToSend = str(t) + "s \t\t" + str(temp) + "\t\t" + str(tempCon ) + " \t C" + "\t" + str(light)
                #time at which reading was made.
                readingTime = str(datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S"))
                completeMessage = readingTime + " " + messageToSend

                clientSocket.send(completeMessage.encode())
                
                t += delay
                time.sleep(delay)