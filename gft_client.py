#!/usr/bin/python3
import re
import socket
import sys
from optparse import OptionParser
from hashlib import md5

def human_size (v):
    kb = v  / 1024
    mb = kb / 1024
    gb = mb / 1024
    res = ""
    if kb < 1024:
        return ("%.2f KB" % kb)
    if mb < 1024:
        return ("%.2f MB" % mb)
    return ("%.2f GB" % gb)

def red (txt):
    return "\033[31;4;1m" + txt + "\033[m"

def green (txt):
    return "\033[32;1m" + txt + "\033[m"

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
parser.add_option ('-a', '--all', dest = 'all',
                   default = False, action = "store_true",
                   help = 'Download all files')

(opts, args) = parser.parse_args ()

if opts.host == None:
    print ("No host specified!")
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
        if c == bytes ('}', "UTF-8"):
            break
    return buff

def parse_inst (inst):
    inst = str (inst, "UTF-8")
    pp = r'{([a-zA-Z0-9]+)(?:=(.*?))?}'
    inst_patt = re.compile (pp)
    return inst_patt.findall (inst)[0]

def download (n, maxl=20):    
    sock.sendall (bytes ("{DOWNLOAD %d}\n" % n,
                         "UTF-8"))

    filesize = 0
    filename = ''
    while 1:
        raw_inst = read_instruct (sock)
        #print (raw_inst)
        sys.stdout.flush ()
        inst = parse_inst (raw_inst)
        #print (inst)
        (inst, arg) = (inst[0].upper (), inst[1])
        if inst == 'SIZE':
            filesize = int (arg)
            #print ("Filesize: %d" % filesize)
        elif inst == 'NAME':
            filename = arg
            #print ("Filename: %s" % filename)
        elif inst == 'HASH':
            checksum = arg
        elif inst == 'BEGIN':
            base_str = ("Getting: name=[" + ("%%%ds" % maxl) + "] [%8s] ") % \
                       (filename, human_size (filesize))
            print (base_str, end = '\r')
            sys.stdout.flush ()
            to_get = filesize
            got = 0
            buff = b''
            sock.setblocking (True)
            with open (filename, 'wb') as ff:
                while got != filesize:
                    getting = min (to_get, 1024)
                    #print (getting)
                    buff = sock.recv (getting,
                                      socket.MSG_WAITALL)
                    got += len (buff)
                    ff.write (buff)
                    ff.flush ()
                    to_get -= getting
                    percentage = (got / filesize) * 100
                    print (base_str + ("%3.2f %%" % percentage), end = '\r')
                    sys.stdout.flush ()
                print (base_str + "100 %", end = ' ')
                sys.stdout.flush ()

            sys.stdout.flush ()

            #print (got)
            calculated = md5 (open (filename,'rb').read ()).hexdigest ()
            #print ("Hash:", checksum)
            #print ("Calc:", calculated)
            if checksum != calculated:
                print (red ("MISMATCH!!"))
            else:
                print (green ("Match!"))
        elif inst == 'END':
            break

def list_all ():
    sock.sendall (bytes ("{LIST}\n", "UTF-8"))
    filelist = []
    while 1:
        raw_inst = read_instruct (sock)
        #print (raw_inst)
        inst = parse_inst (raw_inst)
        filelist.append (inst)
        print (inst)
        if inst[0] == 'END':
            break
    sock.close()
    return filelist
        
if opts.list:
    # do the list thingy
    list_all ()
    sock.close ()
    sys.exit (0)
    
if opts.download == None and (not opts.all):
    print ("No download specified!")
    sys.exit (-1)

if opts.all:
    # download all files
    filelist = list_all ()
    fsize = 0
    fi = 0
    maxl = 0
    for f in filelist:
        if f[0] == 'LIST':
            fsize = int (f[1])
        elif f[0] == 'END':
            break
        else:
            if len (f[1]) > maxl:
                maxl = len (f[1])
    #print (maxl)

                
    for f in filelist:
        if f[0] == 'LIST':
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect ((HOST, PORT))
            fsize = int (f[1])
        elif f[0] == 'END':
            sock.close ()
            break
        else:
            if fi < fsize:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect ((HOST, PORT))
            fi += 1
            ind = f[0]
            # print ("Downloading [%s]" % f[1])
            download (int (f[0]), maxl=maxl)
    
else:
    download (opts.download)
