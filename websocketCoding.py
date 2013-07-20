__author__ = 'selcuk'
import struct
FINAL = 128
TEXT = 1
CONT = 15
MASKED = 128
frag = {}
def decode(client,data):
    totalSize = len(data)
    masked = False
    final = False
    text = False
    cont = False
    msg = 'long'
#    print "len:", len(data[:2])
    a,b = struct.unpack('BB',data[:2])
#    print "a:", a, "b", b
    if(a & FINAL):
        print "FINAL"
        final = True
    else: print "Not Final"
    if (a & TEXT):
        print "TEXT"
        text = True
    elif (a & CONT) == 0:
        print "Continuation"
        cont = True
    else: print "Non-Text"
    if (b&MASKED):
        print "MASKED"
        masked = True
    else: print "No Mask"
    lenFlag = b - 128
    length = 0
    nextIndex = 0
#    print "lenFlag", lenFlag
    if lenFlag <=125:
        length = lenFlag
        nextIndex = 2
    elif lenFlag == 126:
        length = struct.unpack('>H',data[2:4])[0]
        nextIndex = 4
    elif lenFlag > 126:
        length = struct.unpack('>Q',data[2:10])[0]
        nextIndex = 10
    rawLen = len(data)
    unmasked = []
    if masked:
        textIndex = nextIndex + 4
        length = rawLen - textIndex

        maskKey = struct.unpack_from('B'*4, data[nextIndex:nextIndex+4])
#        print maskKey
#        print "Partitioned Length:", length
        masked = data[textIndex:textIndex+length]
#        print "Length of masked:", len(masked)
        for i in range(length):
            unmasked.append(chr(ord(masked[i]) ^ maskKey[i%4]))
        msg =  ''.join(unmasked)
        if final:
            if client in frag.keys():
                msg = frag[client] + msg
                frag[client]=""
                print msg
        else:
            if client in frag.keys():
                frag[client] += msg
            else:
                frag[client] = msg
            msg = ""
    else:
        textIndex = nextIndex
        length = rawLen - textIndex
        msgHex = data[textIndex:textIndex+length]
        for i in range(length):
            unmasked.append(chr(ord(msgHex[i])))
        msg =  ''.join(unmasked)
    return msg
def encode(client, data):
#    print "ENCODING"
    msgSize = len(data)
#    print "size:{0} hex:{0:x}".format(msgSize)
    message=''
    if msgSize<126:
        sizeChr = chr(msgSize)
        message = "\x81%s%s" % (sizeChr,data)
    elif msgSize >= 126 and msgSize<=65535:
        message = struct.pack(">BBH",129,126,msgSize)

        message += data
    elif msgSize > 65535:
        message = struct.pack(">BBQ",129,127,msgSize)

        message += data
    print "ENCODING COMPLETED"
    return  message




