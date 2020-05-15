import socket
import threading
from time import sleep

def ResetMaxMessages():
    global maxMessages
    sleep(1)
    maxMessages = 0

def heartbeat(client, lock):
    while True:
        sleep(3)
        lock.acquire()
        client.send("con-h 0x00".encode())
        lock.release()

def threaded(client, lock):
    global maxMessages
    maxMessages = 0
    msgNumber = 0
    previousMsgNumber = 0

    while True:
        if maxMessages <= selectedMaxMessages:
            text = input()
            lock.acquire()
            #client.send(("msg-" + str(msgNumber) + "=" + text).encode())
            #Trying to send a message without the correct protocol
            client.send(("msg-" + "Hackerman").encode())

            lock.release()
            previousMsgNumber = msgNumber
            msgNumber = previousMsgNumber + 2
            maxMessages = maxMessages + 1

        data = client.recv(4096)

        from_server = data.decode()
        print(from_server)

        if from_server.startswith("con-res 0xFE"):
            client.close()
            print("Timeout occured")
        if not from_server.startswith("res-" + str(msgNumber - 1)):
            client.close()
            print("Protocol ended")

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
    optionsfile()
    readFromConfigFile()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((socket.gethostname(), 4000))
    client.send(("com-0 " + socket.gethostbyname(socket.gethostname())).encode())
    #Trying to create a handshake with a wrong message
    #client.send(("com-1 " + socket.gethostbyname(socket.gethostname())).encode())

    from_server = client.recv(4096)
    print(from_server.decode())

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