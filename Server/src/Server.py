# This will serve as the webserver which will communicate with the client side.
from flask import Flask, app, render_template, request, send_file
import socket
import threading
import sys
import datetime
import json
import os
import csv
import time

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
local_url = '172.20.10.4'  # I shouldn't forget to replace this with the pi address
# local_url = '127.0.0.1'
serverSocket.bind((local_url, 1234))
serverSocket.listen(1)
global clientRepresentative
clientRepresentative = None
userInstruction = 'Deactivate'
client_status = 'OFF'
flag='OFF'
sensorLog = []  # contains information obtained during session from clientside application.
title = ["Date_&_Time", "Temp", "TempDegrees","LDR"]
app = Flask(__name__)


# function to handle messages coming from the client application.
def incomingClientMessages(clientRepresentative):
    global sensorLog
    global client_status
    while True:
        data = clientRepresentative.recv(2048).decode()
        print (data)
        if data != 'ACK' and data != 'ON':
            sensorLog.append(data)
        elif data == 'ON':
            client_status = 'ON'

@app.route("/", methods=['GET', 'POST'])
def htmlOptions():
    global userInstruction
    global clientRepresentative
    global client_status
    global flag
    if request.method == 'POST':
        if request.form.get('Activate') == 'Activate':  #turn on sensors
            userInstruction = 'Activate'  # set the command that will be sent to the client application.
            clientRepresentative.send(userInstruction.encode())  # send command to the client application to
            # turn on sensors and begin transmitting data.
            print ("Activate")

        elif request.form.get('Deactivate') == 'Deactivate':# turn off sensors
            userInstruction = 'Deactivate'
            clientRepresentative.send(userInstruction.encode())
            print ('Deactivate')

        elif request.form.get('Check Status') == 'Check Status':# check status
            clientRepresentative.send('Check Status'.encode())
            print ("Check Status")
            time.sleep(2)
            flag=client_status
            client_status = 'OFF'
            return render_template("SensorApp.html", flag = flag, userInstruction = userInstruction)

        elif request.form.get('CheckLog') == 'CheckLog':
            print ("checking log")
            if (len(sensorLog) > 10):
                return render_template("SensorApp.html", title = title, sensorLog=sensorLog[-10:],userInstruction=userInstruction)
            else:
                return render_template("SensorApp.html", title = title, sensorLog = sensorLog,userInstruction=userInstruction)

        elif request.form.get('DownloadLog') == 'DownloadLog':
            delimiter='\t'
            with open('Log.csv', 'w', encoding='UTF8', newline='') as file:
                writer = csv.writer(file, delimiter=delimiter, quoting=csv.QUOTE_NONE, quotechar='',  lineterminator='\n')
                # writing sensor log
                for row in sensorLog:
                    log=row.split()
                    writer.writerow(log)
            print("downloading")
            path = os.getcwd()+"/Log.csv"
            return send_file(path, as_attachment=True)

        elif  request.form.get('Exit') == 'Exit':# exit process
            print("Exit")
            userInstruction = "Deactivate"
            clientRepresentative.send(userInstruction.encode())
            clientRepresentative.send("Exit".encode())
            sys.exit()
        else:
            return render_template("SensorApp.html", userInstruction = userInstruction)

    elif request.method == 'GET':
        print ("No back call!")
    return render_template("SensorApp.html",userInstruction = userInstruction)
       
    

if __name__ == '__main__':
    kwargs = {'host': local_url, 'port':80, 'threaded': True, 'use_reloader': False, 'debug': False}

    flaskThread = threading.Thread(target=app.run, daemon=True, kwargs=kwargs).start()

    # initiate the connection with the client and begin listening.
    while True:
        print ("trying to connect")
        
        clientRepresentative, clientAddress = serverSocket.accept()  # setup connection.
        print ("Client is :".format(str(clientAddress)))
        clientRepresentative.send(userInstruction.encode('ascii'))  # transmit the instruction for the client application.
        clientThread = threading.Thread(target=incomingClientMessages, args=(clientRepresentative,))  # use thread to listen to data being transmitted from client.
        clientThread.start()  # start the thread.
