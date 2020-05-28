import socket
import threading
from time import sleep
import datetime

def timeout():
    global clientTimeout
    while True:
        sleep(4)

        #Resets connection if client has enabled heartbeat
        if from_client.startswith("con-h 0x00"):
            clientTimeout = False

        print("in timeout " + str(clientTimeout))

        #If clientTimeout == True: send connection reset message
        #If clientTimeout == False: Set it = true and sleep for 4 seconds
        if clientTimeout:
            connection.send(("con-res 0xFE").encode())
        else:
            clientTimeout = True

def threaded():
    global clientTimeout
    global from_client
    from_client = ''
    msgNumber = 1
    handshake = False

    while True:
        data = connection.recv(4096)
        clientTimeout = True

        from_client = data.decode()
        print(from_client)

        #Checks if incoming messages breaks protocol or if the connection needs to be closed
        if not from_client.startswith("msg-0"):
            clientTimeout = False
            #Checks for timeout
            if from_client == "con-res 0xFF":
                connection.close()
                print("Connection timed out...")
                break
            #Checks if message breaks protocol
            if not from_client.startswith("com-0") and not from_client.startswith("con-h 0x00") and ((msgNumber - extractNumber(from_client)) != 1):
                connection.close()
                print("Corrupt/false data received - Socket closed")
                break

        #Performs Handshake
        if not handshake:
            if from_client.startswith("com-0 ") and not from_client.startswith("com-0 accept") and int(from_client[7:9]) in range(0, 256):
                clientTimeout = False
                connection.send(("com-0 accept " + socket.gethostbyname(socket.gethostname())).encode())

            if from_client == "com-0 accept":
                clientTimeout = False
                handshake = True
                writeToLog()

        #Checks for correct message number and replies the client
        if from_client.startswith("msg-") and ((msgNumber - extractNumber(from_client)) == 1):
            clientTimeout = False
            connection.send(("res-" + str(msgNumber) + "=I AM SERVER").encode())
            msgNumber = msgNumber+2

        from_client = ''


def writeToLog():
    with open("log.txt", "a") as file:
        print(str(datetime.datetime.now()) + " successful handshake performed")
        file.write(str(datetime.datetime.now()) + " successful handshake performed \n")
        file.close()


def extractNumber(from_client):
    global clientNumber
    if not from_client.startswith("com-0"):
        string = from_client.replace('msg-', '', 1).replace('=', ' ', 1)
        numberSearch = [int(i) for i in string.split() if i.isdigit()]
        clientNumber = numberSearch[0]
        return int(clientNumber)

def Main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((socket.gethostname(), 4000))
    server.listen(4)

    print("Listening...")
    while True:
        global connection
        connection, addr = server.accept()
        threading.Thread(target=threaded).start()
        threading.Thread(target=timeout).start()

Main()