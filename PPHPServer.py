from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler #base server OP
import urlparse, cgi, os, threading, sys, time #necessary
from pphp import do #the whole point of this package

class handler(BaseHTTPRequestHandler): #request handler
    if len(sys.argv) > 1:
        root = sys.argv[1].strip('"')
    else:
        root = raw_input('Enter path to root directory: ')
    def do_GET(self): #get requests
        try:
            pth = urlparse.urlparse(self.path) #path object
            path = pth.path #path string without anything else
            path = self.indexify(path) #add index.something if it's a dir
            if path is None: #if file not found by indexify
                raise IOError('File not found') #catch that
            f = open(path) #get the file
            self.send_response(200) #send ok, no error was raised
            self.end_headers() #thats all the headers
            self.wfile.write(do(f.read(), #contents of file
                                _GET=urlparse.parse_qs(pth.query), #get data
                                _REQUEST=dict(urlparse.parse_qs(pth.query).items()), #for consistency with PHP's $_REQUEST
                                _SERVER={'PPHP_SELF': path, #path to file
                                         'GATEWAY_INTERFACE': cgi.__version__, #inconsistent with PHP
                                         'SERVER_ADDR': self.server.server_address[0], #server address
                                         'SERVER_NAME': self.server.server_name, #server name
                                         'SERVER_SOFTWARE': 'PPHP/1.2', #server version (pphp)
                                         'SERVER_PROTOCOL': self.protocol_version, #protocol version
                                         'REQUEST_METHOD': self.command, #request method
                                         'QUERY_STRING': pth.query, #query string
                                         'REMOTE_ADDR': self.client_address[0], #client ip
                                         'REMOTE_PORT': self.client_address[1], #client port
                                         'SERVER_PORT': self.server.server_address[1] #server port
                                         }
                                )) #whoo
            f.close() #close for completeness
        except IOError: #file not found
            self.send_error(404) #send not found error
            self.end_headers() #end headers
    def do_POST(self): #post requests
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type')) #parse post headers
        if ctype == 'multipart/form-data': #if this is multipart form data
            postvars = cgi.parse_multipart(self.rfile, pdict) #parse data
        elif ctype == 'application/x-www-form-urlencoded': #if this is application form data
            length = int(self.headers.getheader('content-length')) #get length of data
            postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1) #read length bytes of data (all the bytes)
        else: #not recognized
            postvars = {} #empty post data
        try:
            pth = urlparse.urlparse(self.path) #path object
            path = pth.path #path string without anything else
            path = self.indexify(path) #and so on
            if path is None:
                    raise IOError
            f = open(path)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(do(f.read(),
                                _GET=urlparse.parse_qs(pth.query),
                                _POST=postvars, #pass post vars too
                                _REQUEST=dict(urlparse.parse_qs(pth.query).items()+postvars.items()), #and make _REQUEST include postvars as well
                                _SERVER={'PPHP_SELF':path,
                                         'GATEWAY_INTERFACE':cgi.__version__,
                                         'SERVER_ADDR':self.server.server_address[0],
                                         'SERVER_NAME':self.server.server_name,
                                         'SERVER_SOFTWARE':self.server_version,
                                         'SERVER_PROTOCOL':self.protocol_version,
                                         'REQUEST_METHOD':self.command,
                                         'QUERY_STRING':pth.query,
                                         'REMOTE_ADDR':self.client_address[0],
                                         'REMOTE_PORT':self.client_address[1],
                                         'SERVER_PORT':self.server.server_address[1]
                                         }
                                ))
            f.close()
        except IOError:
            self.send_error(404)
            self.end_headers()
    def indexify(self, path):
        if os.path.isdir(self.root+path): #if the path is a directory
            if not path.endswith('/'): #check if the path ends with /
                path += '/' #make sure it does
            for index in ["index.html", "index.htm"]: #only current possibilities for names
                index = os.path.join(self.root+path, index) #join path and index type
                if os.path.exists(index): #if that file exists
                        path = index #path becomes full path
                        return path #return full path
            if path != index: #if no matches were found
                return None #None is handled by the dos
        else: #if it wasn't even a dir
            return self.root+path #return it as is with the root

lock = threading.Lock() #lock object for synchronization

if len(sys.argv) > 2: #if we have a second argument
    addr, ports = sys.argv[2].split(':') #format is IP:(portmin, portmax[, portstep])
else: #if we don't have a second argument
    addr, ports = raw_input('Enter IP:(portmin, portmax[, portstep]) to use: ').split(':') #get input from console or whatever

def serve(port): #function to serve one port
    global lock, addr #lock object needs to be global; address needs to be consistent
    with lock: #for synced handling
        httpd = HTTPServer((addr, port), handler) #start the server
        print 'Serving %s on port %s...' % httpd.server_address #log starting server
    while 1: #forever
        with lock: #for synced handling
            httpd.handle_request() #handle one request
    with lock: #this will never happen
        print 'Stopping server on %s:%s...' % httpd.server_address #log stopping server

for i in range(*eval(ports, {'__builtins__':{}})): #for every port specified (evaluate tuple)
    t = threading.Thread(target=serve,args=(int(i),)) #new thread for each port (make i an int)
    t.daemon = True #so that Ctrl-C can stop it (ugly, I know)
    t.start() #start the thread
print 'Press Ctrl-C to stop all servers.' #log how to stop
while 1: #then keep the main thread open
    try:
        time.sleep(1) #for termination
    except KeyboardInterrupt: #catch it
        raise SystemExit #raise this instead to make it less ugly
