# This will serve as the webserver which will communicate with the client side.
from flask import Flask, app, render_template, request, send_file
import socket
import threading
import sys
from datetime import datetime
import json
import os
import csv
import time

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
local_url = '172.20.10.4'  # I shouldn't forget to replace this with the pi address
serverSocket.bind((local_url, 1234))
serverSocket.listen()
global clientRepresentative
clientRepresentative = None
userInstruction = 'DeactivateSensors'
client_status = "OFF"
sensorLog = []  # contains information obtained during session from clientside application.
lastindex = 0
title = ["No.", "Date_&_Time", "Temperature Readings", "LDR Readings"]

app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def htmlOptions():
    global userInstruction
    global clientRepresentative
    if request.method == 'POST':
        if request.form.get('Activate') == 'Activate Sensors':
            userInstruction = 'ActivateSensors'  # set the command that will be sent to the client application.
            clientRepresentative.send(userInstruction.encode())  # send command to the client application to
            # turn on sensors and begin transmitting data.
            print (userInstruction)
        elif request.form.get('Deactivate') == 'Deactivate Sensors':
            userInstruction = 'Deactivate Sensors'
            clientRepresentative.send(userInstruction.encode())
            print ('Deactivate Sensors')
        elif request.form.get('Turn off') == 'Turn Off':
            client_status = 'OFF'
            clientRepresentative.send(client_status.encode())
            print ("Turn Off")
            time.sleep(2)
            return render_template("SensorApp.html", client_status, userInstruction)
        elif request.form.get('CheckLog') == 'CheckLog':
            print ("checking log")
            if len(sensorLog) > 10:
                return render_template("SensorApp.html", title, sensorLog=sensorLog[-10])
            else:
                return render_template("SensorApp.html", title, sensorLog)
        elif request.form.get('DownloadLog') == 'DownloadLog':
            with open('Log.csv', 'w', encoding='UTF8', newline='') as f:
                writer = csv.writer(f)
                # Writing the titles
                writer.writerow(title)
                # writing sensor log
                for row in sensorLog:
                    writer.writerow(row)
            print("downloading")
            path = os.getcwd()+"/Log.csv"
            return send_file(path, as_attachment=True)
        elif request.form.get('Clear') == 'Clear Log':
            sensorLog.clear()
            return render_template("SensorApp.html", sensorData=sensorLog)
        elif  request.form.get('Exit') == 'Exit':
            print("Exit")
            userInstruction = "Turn Off Sensors"
            clientRepresentative.send(userInstruction.encode())
            clientRepresentative.send("exit".encode())
            sys.exit()
        else:
            return render_template("SensorApp.html", userInstruction)
    elif request.method == 'GET':
        # print ("No back call!")
        pass
    return render_template("SensorApp.html",userInstruction)


# function to handle messages coming from the client application.
def incomingClientMessages(clientRepresentative):
    global sensorLog
    global client_status
    while True:
        data = clientRepresentative.recv(2048).decode()
        if data != 'SENDACK' and data != 'ON':
            sensorLog.append(data)
        elif data == 'ON':
            client_status = 'ON'
        print (data)
        # sensorLog.append(
        #     clientRepresentative.recv(2048).decode())  # append data from client side application to the log.
        #


# function to constantly update the log data.
@app.route("/logData", methods=['GET', 'POST'])
def updateLog():
    if request.method == 'POST':
        return render_template("SensorApp.html", sensorData=sensorLog)
    elif request.method == 'GET':
        pass
    return render_template("SensorApp.html", sensorData=sensorLog)
    # updatedData = make_response(json.dumps(sensorLog)) #package data into json for transmission to the webpage.
    # updatedData.content_type = 'application/json'
    # return updatedData # send data to the webpage.


if __name__ == '__main__':

    # initiate the connection with the client and begin listening.
    while True:
        print ("trying to connect")
        clientRepresentative, clientAddress = serverSocket.accept()  # setup connection.
        print ("Client is :".format(str(clientAddress)))
        clientRepresentative.send(
            userInstruction.encode('ascii'))  # transmit the instruction for the client application.
        clientThread = threading.Thread(target=incomingClientMessages, args=(
            clientRepresentative,))  # use thread to listen to data being transmitted from client.
        clientThread.start()  # start the thread.

    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=80, debug=True, use_reloader=False)).start()
