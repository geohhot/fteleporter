import re
import socket
import sys
from optparse import OptionParser

parser = OptionParser ()

parser.add_option ('-l', '--list', dest = 'list',
                   default = False, action = "store_true",
                   help = "List the files available")
parser.add_option ('-d', '--download', dest = 'download',
                   type = "int",
                   help = "File to download")
parser.add_option ('-s', '--host', dest = 'host',
                   help = 'The host to connect to')
parser.add_option ('-p', '--port', dest = 'port',
                   type = 'int',
                   help = 'Port to connect to')

(opts, args) = parser.parse_args ()

if opts.host == None:
    print ("No host!")
    sys.exit (-1)

spl = opts.host.split (':') 
if len (spl) == 2:
    HOST = spl[0]
    PORT = int (spl[1])

else:
    if opts.port == None:
        print ("No port!")
        sys.exit (-1)
    HOST = opts.host
    PORT = opts.port

print ((HOST, PORT))

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect ((HOST, PORT))

def read_instruct (sock):
    buff = b''
    while 1:
        c = sock.recv (1)
        buff += c
        if c == b'}':
            break
    return buff

def parse_inst (inst):
    inst = str (inst, "ASCII")
    pp = r'{([a-zA-Z0-9]+)(?:=([a-zA-Z0-9\./_]+))?}'
    inst_patt = re.compile (pp)
    return inst_patt.findall (inst)[0]

if opts.list:
    # do the list thingy
    sock.sendall (bytes ("{LIST}\n", "ASCII"))
    while 1:
        raw_inst = read_instruct (sock)
        #print (raw_inst)
        inst = parse_inst (raw_inst)
        print (inst)
        if inst[0] == 'END':
            break
    sock.close()
    sys.exit (0)

if opts.download == None:
    print ("No download specified!")
    sys.exit (-1)

sock.sendall (bytes ("{DOWNLOAD %d}\n" % opts.download,
                     "ASCII"))

filesize = 0
filename = ''
while 1:
    raw_inst = read_instruct (sock)
    #print (raw_inst)
    inst = parse_inst (raw_inst)
    print (inst)
    (inst, arg) = (inst[0].upper (), inst[1])
    if inst == 'SIZE':
        filesize = int (arg)
    elif inst == 'NAME':
        filename = arg
    elif inst == 'BEGIN':
        to_get = filesize
        buff = b''
        with open (filename, 'wb') as ff:
            while 1:
                getting = min (to_get, 1024)
                buff = sock.recv (getting)
                if to_get == 0:
                    break
                ff.write (buff)
                to_get -= getting
    elif inst == 'END':
        break


    



