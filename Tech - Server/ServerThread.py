import socket
import threading
from time import sleep
import datetime

def timeout():
    global clientTimeout
    while True:
        sleep(4)

        if from_client.startswith("con-h 0x00"):
            clientTimeout = False

        print("in timeout " + str(clientTimeout))

        if clientTimeout:
            conn.send(("con-res 0xFE").encode())
            sleep(1.0)
            print("Connection timed out...")
            conn.close()
        else:
            clientTimeout = True

def threaded():
    global clientTimeout
    global from_client
    from_client = ''
    msgNumber = 1
    previousMsgNumber = 1

    while True:
        data = conn.recv(4096)
        clientTimeout = True
        from_client = data.decode()
        print(from_client)

        if not from_client.startswith("msg-0"):
            clientTimeout = False
            if not from_client.startswith("msg-" + str(msgNumber - 1)) and not from_client.startswith("com-0") and not from_client.startswith("con-h 0x00"):
                conn.close()
                print("Corrupt/false data received - Socket closed")
                break

        if from_client.startswith("com-0 accept"):
            with open("log.txt", "a") as file:
                file.write(str(datetime.datetime.now()) + " successful handshake performed \n")
                print(str(datetime.datetime.now()) + " successful handshake performed")
                file.close()

        if from_client.startswith("com-0 ") & from_client.__contains__("."):
            clientTimeout = False
            conn.send(("com-0 accept " + socket.gethostbyname(socket.gethostname())).encode())

        if from_client.startswith("msg-"):
            clientTimeout = False
            previousMsgNumber = msgNumber
            conn.send(("res-" + str(msgNumber) + "=I AM SERVER").encode())
            msgNumber = previousMsgNumber + 2

        from_client = ''

def Main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((socket.gethostname(), 4000))
    server.listen(4)

    print("Listening...")
    while True:
        global conn
        conn, addr = server.accept()
        threading.Thread(target=threaded).start()
        threading.Thread(target=timeout).start()

Main()