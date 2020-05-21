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

def threaded(connection, lock):
    global maxMessages
    maxMessages = 0
    msgNumber = 0

    while True:
        if maxMessages <= selectedMaxMessages:
            text = input()

            lock.acquire()
            connection.send(("msg-" + str(msgNumber) + "=" + text).encode())
            lock.release()

            maxMessages = maxMessages + 1
            msgNumber = msgNumber + 2

        data = connection.recv(4096)
        from_server = data.decode()
        print(from_server)

        if from_server == "con-res 0xFE":
            connection.close()
            print("Timeout occured...")
            break

        if not from_server.startswith("res-") and not ((msgNumber - extractNumber(from_server)) == 1):
            connection.close()
            print("Protocol corrupted - connection ended...")
            break

def extractNumber(from_server):
    global serverNumber
    if not from_server.startswith("com-0"):
        string = from_server.replace('res-', '', 1).replace('=', ' ', 1)
        numberSearch = [int(i) for i in string.split() if i.isdigit()]
        serverNumber = numberSearch[0]
        return int(serverNumber)

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