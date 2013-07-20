#!/usr/bin/env python

import socket, struct, hashlib, threading, cgi, base64
from websocketCoding import decode, encode
FINAL = 128
TEXT = 1
CONT = 15
MASKED = 128

def createHash (key, code):
    a = key.strip()
    b = code.strip()
    mySHA = hashlib.sha1(a + b)
    return base64.b64encode(mySHA.digest())

def recvData (client, length):
    data = client.recv(length)
    return data
def sendData (client, data):
    try:
        client.send(data)
    except:
        print "Unexpected error in send_data function"

def parseHeaders (data):
    headers = {}
    lines = data.splitlines()
    for l in lines:
        pair = l.split(": ", 1)
        if len(pair) == 2:
            headers[pair[0]] = pair[1]
    return headers

def handShake (client):
    print 'Handshaking...'
    data = client.recv(1024)
    headers = parseHeaders(data)
    print 'Got headers:'
    for k, v in headers.iteritems():
        print k, ':', v
    digested = createHash(
        headers['Sec-WebSocket-Key'],
        "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    )
#    print "digest:", digested
    websocket_answer = (
    'HTTP/1.1 101 Switching Protocols',
    'Upgrade: websocket',
    'Connection: Upgrade',
    'Sec-WebSocket-Accept: {key}\r\n\r\n',
    )
    response = '\r\n'.join(websocket_answer).format(key=digested)
    return client.send(response)

def getMsgSize(data):
    length = 0
    headerSize = 0
    maskSize = 0
    a,b = struct.unpack('BB',data[:2])
    if (b&MASKED):
#        print "MASKED"
        maskSize = 4
    lenFlag = b - 128
    if lenFlag <=125:
        length = lenFlag
        headerSize = 2
    elif lenFlag == 126:
        length = struct.unpack('>H',data[2:4])[0]
        headerSize = 4
    elif lenFlag > 126:
        length = struct.unpack('>Q',data[2:10])[0]
        headerSize = 10
    return headerSize + maskSize + length


def socketRecv(client, bufLen = 1024):
    peekData = client.recv(bufLen, socket.MSG_PEEK)
    if peekData:
        realSize = getMsgSize(peekData)
        remaining = realSize
        realData = ""
        try:
            while (remaining>0):
                realBuffer = min(remaining, 30000)
                print "reading %s bytes" % realBuffer
                realData += client.recv(realBuffer)
                remaining -= realBuffer
        except:
            print "Unexpected error in socketRecv function"
        return realData
    else:
        return peekData




def handle (client, addr):
    handShake(client)
    lock = threading.Lock()
    while 1:
        data = socketRecv(client)
        if data:
            if (ord(data[:1]) & 15) == 8:
                break
            else:
                lock.acquire()
                data = decode(client,data)
                data = cgi.escape(data)
#                print "Received Data:", data, len(data)
                data = encode(client,data)
                print "TOTAL Clients", len(clients)
                [sendData(c, data) for c in clients]
#                print "Sent Data:", data.encode('hex')
                lock.release()
    print 'Client closed:', addr
    lock.acquire()
    clients.remove(client)
    lock.release()
    client.close()

def start_server ():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 9876))
    s.listen(5)
    while 1:
        conn, addr = s.accept()
        print 'Connection from:', addr
        clients.append(conn)
        threading.Thread(target = handle, args = (conn, addr)).start()

clients = []
start_server()