import socket
import threading
from time import sleep

#Handles the max number of messages allowed to be sent
def ResetMaxMessages():
    global maxMessages
    sleep(1)
    maxMessages = 0

#Keeps connection alive
def heartbeat(client, lock):
    while True:
        sleep(3)
        lock.acquire()
        client.send("con-h 0x00".encode())
        lock.release()
        clientTimeout = False

#Handles user input and server respond
def threaded(connection, lock):
    global maxMessages
    maxMessages = 0
    msgNumber = 0

    while True:
        if maxMessages <= selectedMaxMessages:
            text = input()

            lock.acquire()

            #connection.send(("msg-" + str(msgNumber) + "=" + text).encode())

            #Trying to send a message without the correct protocol
            connection.send(("msg-" + "Hackerman").encode())

            lock.release()

            maxMessages = maxMessages + 1
            msgNumber = msgNumber + 2


        data = connection.recv(4096)
        from_server = data.decode()
        print(from_server)

        #If server responds with this message the connection is closed
        if from_server == "con-res 0xFE":
            connection.send("con-res 0xFF".encode())
            sleep(1)
            connection.close()
            print("Timeout occured...")
            break

        #Checks if the messages coming from the server follows the protocol
        if not from_server.startswith("res-") and not ((msgNumber - extractNumber(from_server)) == 1):
            connection.close()
            print("Protocol corrupted - connection ended...")
            break

#Extracts the message number from the server message and returns it
def extractNumber(from_server):
    global serverNumber
    if not from_server.startswith("com-0"):
        string = from_server.replace('res-', '', 1).replace('=', ' ', 1)
        numberSearch = [int(i) for i in string.split() if i.isdigit()]
        serverNumber = numberSearch[0]
        return int(serverNumber)

#Asks user about custom options
def optionsfile():
    file = open("opt.conf")
    data = file.readlines()

    print("Do you wish to keep connection alive? (y/n)")
    if input().startswith("y"):
        data[0] = "keepAlive : True\n"
    else:
        data[0] = "keepAlive : False\n"

    print("Change packages sent pr. second (Default = 25)? (y/n)")
    if input().startswith("y"):
        print("Maximum number of packages pr. second: ")
        data[1] = "maxMessages : " + input() + "\n"
    else:
        data[1] = "maxMessages : 25\n"

    with open("opt.conf", "w") as file:
        file.writelines(data)

#Reads custom options from file
def readFromConfigFile():
    global selectedMaxMessages
    global keepAlive

    file = open("opt.conf")
    allLines = file.readlines()

    if allLines[0].__contains__("True"):
        keepAlive = True
    else:
        keepAlive = False

    selectedMaxMessages = int(allLines[1][13:17])

def Main():
    #Handles user options for the connection
    optionsfile()
    readFromConfigFile()

    #Creates a socket and attempt to connect to server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((socket.gethostname(), 4000))
    client.send(("com-0 " + socket.gethostbyname(socket.gethostname())).encode())

    #Trying to create a handshake with a wrong message
    #connection.send(("com-1 " + socket.gethostbyname(socket.gethostname())).encode())

    from_server = client.recv(4096)
    print(from_server.decode())

    #Checks for server response and setup connection on client side
    if from_server.decode().startswith("com-0 accept"):
        client.send("com-0 accept".encode())

        lock = threading.Lock()
        threading.Thread(target=threaded, args=(client, lock,)).start()
        threading.Thread(target=ResetMaxMessages).start()
        if keepAlive:
            threading.Thread(target=heartbeat, args=(client, lock,)).start()
    else:
        client.close()

Main()