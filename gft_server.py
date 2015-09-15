import os
import socketserver
import re

gft = re.compile (r'^{([a-zA-Z0-9\s]*[a-zA-Z0-9])}[\n\r]+')
#r"^{(.*)}[\r]?$")
    
class GFTServer (socketserver.StreamRequestHandler):
    def sendout (self, data):
        self.wfile.write (bytes (data, "ASCII"))

    def get_filelist (self):
        # prints out the file
        filelist = []
        with open ('filelist.txt', 'r') as fl:
            while 1:
                line = fl.readline ()
                if not line:
                    break
                if line.strip():
                    filelist.append (line.strip())
        print ("Filelist: ", filelist)
        return filelist
        
    def output_filelist (self):
        filelist = self.get_filelist ()
        self.sendout ("{LIST=%d}" % len (filelist))
        index = 1
        for f in filelist:
            self.sendout ("{%d=%s}" % (index, f))
            index += 1
        self.sendout ("{END}")
        self.filelist = filelist

    def error (self, num):
        self.sendout ("{ERRONEOUSCOMMAND=%d}" % num)
        self.sendout ("{END}")    
        
    def upload_file (self, fnum):
        try:
            fnum = int (fnum)
        except ValueError:
            self.error (2)
            return
        filelist = self.get_filelist ()
        if fnum > len (filelist) or fnum < 1:
            self.error (7)
            return
        f = filelist [fnum - 1]
        print ("Uploading file: ", f)
        if not os.path.exists (f):
            self.error (5)
            return
        filesize = os.path.getsize (f)
        (filepath, filename) = os.path.split (f)
        self.sendout ("{SIZE=%d}" % filesize)
        self.sendout ("{NAME=%s}" % filename)
        self.sendout ("{BEGIN}")
        with open (f, 'rb') as fb:
            while 1:
                buff = fb.read (1024)
                if not buff:
                    break
                self.wfile.write (buff)
        self.sendout ("{END}")
        
    def handle (self):
        self.data = self.rfile.readline ()
        data = str (self.data, "ASCII")
        #print ("Data: ", bytes (data, "ASCII"))

        try:
            commands = gft.search (data).group (1)
        except AttributeError:
            self.error (1)
            return

        command = re.split ('\s+', commands)
        print ("Got: ", command)
        if command[0].upper() == "LIST":
            self.output_filelist ()
        elif command[0].upper() == "DOWNLOAD":
            if len (command) > 1:
                self.upload_file (command[1])
            else:
                self.error (4)
                
        #self.wfile.write (bytes (str (command) + '\n', "ASCII"))

if __name__ == "__main__":
    HOST, PORT = "localhost", 7777

    while PORT < 8000:
        try:
            server = socketserver.TCPServer ((HOST,PORT), GFTServer)
            print ("Running on: ", server.server_address)
            
            server.serve_forever ()
        except OSError:
            PORT += 1
        
