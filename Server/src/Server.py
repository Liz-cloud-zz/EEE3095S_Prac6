#This will serve as the webserver which will communicate with the client side.
from flask import Flask, app, render_template, request
import socket
import threading
from datetime import datetime
import json

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
local_url = '127.0.0.1' # I shouldn't forget to replace this with the pi address
serverSocket.bind((local_url,1234))
serverSocket.listen()
global clientRepresentative
clientRepresentative = None
userInstruction = 'DeactivateSensors'
sensorLog = [] #contains information obtained during session from clientside application.
lastindex = 0

app = Flask(__name__)

@app.route("/", methods=['GET','POST'])
def htmlOptions():
    global userInstruction
    global clientRepresentative
    if request.method == 'POST':
        if request.form.get('Activate') == 'Activate Sensors':
            userInstruction = 'ActivateSensors' #set the command that will be sent to the client application.
            clientRepresentative.send(('ActivateSensors').encode()) # send command to the client application to turn on sensors and begin transmitting data.
        elif request.form.get('Deactivate') == 'Deactivate Sensors':
            pass
        elif request.form.get('Clear') == 'Clear Log':
            sensorLog.clear()
            return render_template("SensorApp.html", sensorData=sensorLog)
        elif request.form.get('Download') == 'Download Log':
            pass
    elif request.method == 'GET':
        pass
    return render_template("SensorApp.html")
    
#function to handle messages coming from the client application.
def incomingClientMessages(clientRepresentative):
    global sensorLog
    while True:
        sensorLog.append(clientRepresentative.recv(2048).decode()) # append data from client side application to the log.

    
#function to constantly update the log data.
@app.route("/logData",methods=['GET','POST'])
def updateLog():
    if request.method == 'POST':
        return render_template("SensorApp.html", sensorData=sensorLog)
    elif request.method == 'GET':
        pass
    return render_template("SensorApp.html", sensorData=sensorLog)
    #updatedData = make_reponse(json.dumps(sensorLog)) #package data into json for transmission to the webpage.
    #updatedData.content_type = 'application/json'
    #return updatedData # send data to the webpage.




if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=80, debug=True, use_reloader=False)).start()
    
    #initiate the connection with the client and begin listening.
    while(True):
        
        
        clientRepresentative,clientAddress = serverSocket.accept() #setup connection.
        
        clientRepresentative.send(userInstruction.encode('ascii')) #transmit the instruction for the client application.
        clientThread = threading.Thread(target=incomingClientMessages, args=(clientRepresentative,)) #use thread to listen to data being transmitted from client.
        clientThread.start() #start the thread.