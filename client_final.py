import socket, re, time, threading, configparser

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 10000)

try:

    # Reads config file and sets status of heartbeat
    config = configparser.ConfigParser()
    config.read('opt.conf')

    heartbeatStatus = config.get('HeartbeatStatus', 'keepAlive')

    
    class receivedataThread(threading.Thread):
        data = None
        server = None
        splittedData = None
        message_number = None
        successful_connection = False
        send_block = False

        def __init__(self):
            threading.Thread.__init__(self)

        def run(self):
            while True:
                if self.successful_connection:
                    # Receive data
                    data, self.server = sock.recvfrom(4096)
                    self.data = data.decode()

                    splittedData = re.split('[\s=-]', self.data)
                    splittedData.append(self.server[0])

                    # Checks if it's a message or connection reset message from server
                    if splittedData[0] == 'res' \
                            or splittedData[0] == 'com' \
                            and splittedData[1] == '0' \
                            and splittedData[2] == 'accept' \
                            and splittedData[3] == self.server[0]:

                        # Parsed to an int to make it possible to check it
                        message_number = int(splittedData[1])

                        # Prints message and adds 1 to message number if message isn't part of handshake
                        if message_number > 0:
                            print('[SERVER]: ' + self.data)

                            # Sets message number by adding one to the receivedatad number
                            message_number += 1

                        # Parsed back to string to be able to encode it to bytes
                        self.message_number = str(message_number)

                    elif splittedData[0] == 'con' \
                            and splittedData[1] == 'res' \
                            and splittedData[2] == '0xFE':
                        message = b'con-res 0xFF'
                        sock.sendto(message, server_address)
                        self.successful_connection = False
                        print('[SERVER]: ' + self.data + ": You're disconnected from server " + server_address[0])

                    elif splittedData[0] == 'con' \
                            and splittedData[1] == 'max' \
                            and splittedData[2] == 'lock':
                        if self.send_block == False:
                            print("[CLIENT]: You've reached maximum amount of packages sent. Please wait")

                        # Sets a block on senddata if max number of packages pr second is surpassed
                        self.send_block = True

                    elif splittedData[0] == 'con' \
                            and splittedData[1] == 'max' \
                            and splittedData[2] == 'open':
                        if self.send_block == True:
                            print("[SERVER]: Connection open again")
                        # Unblock senddata package sent from server
                        self.send_block = False

    # Heartbeat Thread
    class heartbeatThread(threading.Thread):
        last_send = None
        
        def __init__(self):
            threading.Thread.__init__(self)
            self.setlastsend()

        def setlastsend(self):
            self.last_send = time.time()
            
        def run(self):
            while (heartbeatStatus == 'true' or heartbeatStatus == 'True'):
                # Checks if it's 3 seconds since last message was sent
                if self.last_send + 3 <= time.time():
                    message = b'con-h 0x00'
                    sock.sendto(message, server_address)
                    self.setlastsend()

    # Function that performs the threeway handshake
    def threewayhandshake():
        message_number = '0'
        successful_connection = False

        # Starts three-way handshake
        message = b'com-0'
        sock.sendto(message, server_address)

        # Receive data
        data, server = sock.recvfrom(4096)
        data = data.decode()

        splittedData = re.split('[\s=-]', data)
        splittedData.append(server[0])

        # Checks if incoming data follows protocol and answers back
        if splittedData[0] == 'com' \
                and splittedData[1] == '0' \
                and splittedData[2] == 'accept' \
                and splittedData[3] == server[0]:

            message = b'com-0 accept'
            sock.sendto(message, server_address)

            successful_connection = True
            print("[CLIENT]: Connected successfully to server", server_address[0])

        return message_number, successful_connection

    def senddata():
        # Delay to make sure the server has time to respond before client sends a new package
        time.sleep(0.1)

        if receivedata.successful_connection and receivedata.send_block is False:
            # Message is sent to server with the incremented message number
            message = b'msg-' + receivedata.message_number.encode() + b'=Hi, server! I am a client'
            print('[CLIENT]: ' + message.decode())
            sock.sendto(message, server_address)
            heartbeat.setlastsend()
        elif receivedata.successful_connection is False:
            print("[CLIENT]: Couldn't send data. Successful connection to server isn't established")

    receivedata = receivedataThread()
    heartbeat = heartbeatThread()
    
    receivedata.start()
    heartbeat.start()

    while True:
        receivedata.message_number, receivedata.successful_connection = threewayhandshake()
        while receivedata.successful_connection:
            for x in range(30):
                senddata()


finally:
    print('closing socket')
    sock.close()