import re, sys, json, os, traceback, cgi
from cStringIO import StringIO
if not '__DATABASE__.json' in os.listdir('.'):
    f = open('__DATABASE__.json', 'w')
    f.write('{}')
    f.close()
def deunicode(d):
    if type(d) != type({}):
        raise TypeError('Expected dict, got ' + str(type(d)))
    for k in d:
        if type(k) == unicode:
            v = d[k]
            del d[k]
            d[str(k)] = v
    return d
def do(html, _GET={}, _POST={}, _REQUEST={}, _SERVER={}):
    __scripts__ = re.findall(r'<\?pphp.*?\?>', html, re.DOTALL) #get all the scripts
    __outputs__ = [] #outputs
    _SERVER['SCRIPT_FILENAME'], _SERVER['PATH_TRANSLATED'] = __file__, __file__
    f = open('__DATABASE__.json', 'r')
    __db__ = json.loads(f.read().strip())
    f.close()
    __pre__ = None #to get around a weird UnboundLocalError
    for __script__ in __scripts__: #for every script
        __pre__ = sys.stdout #backup of sys.stdout so that we can restore it later
        sys.stdout = StringIO() #replace stdout with something we can use to capture stdout
        echo = sys.stdout.write #define keyword echo
        try: exec __script__[7:-2] #execute code (without the tag)
        except:
            sys.stdout.close()
            sys.stdout = __pre__
            html = '<!doctype html><head><title>Error</title><style>* {color:red} div {font-family:monospace}</style></head><body><h1>Exception happened during processing of code</h1><div>'
            trace = traceback.format_exc().split('\n')
            for i in trace:
                html += cgi.escape(i).replace(' ', '&nbsp;')+'<br/>'
            html += '</div>'
            return html
        __output__ = sys.stdout.getvalue() #get stdout value
        sys.stdout.close() #close for completeness
        sys.stdout = __pre__ #restore original stdout
        __outputs__.append(__output__) #store the output
    for out in __outputs__: #for every output
        html = re.sub(r'<\?pphp.*?\?>', str(out), html, count=1, flags=re.DOTALL) #replace each script with its output
    f = open('__DATABASE__.json', 'w')
    f.write(json.dumps(__db__))
    f.close()
    sys.stdout = __pre__
    return html

if __name__ != '__main__':
    sys.exit()

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler #base server OP
import urlparse, threading, time #necessary

class handler(BaseHTTPRequestHandler): #request handler
    if len(sys.argv) > 1: #if we have a first argument
        root = sys.argv[1].strip('"') #get the path from it
    else:
        root = raw_input("Enter path to root directory: ") #ask for it
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
                                _SERVER={'PPHP_SELF': pth.path, #path to file
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
    addr, ports = sys.argv[2].strip('"').split(':') #format is IP:(portmin, portmax[, portstep])
else: #if we don't have a second argument
    addr, ports = raw_input('Enter IP:(portmin, portmax[, portstep]) to use: ').split(':') #get input from console or whatever

ports = eval(ports, {'__builtins___':{}}) #evaluate tuple/list
if type(ports) == type(1): #wait it was int?
    ports = range(ports, ports+1) #make it a list

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

for i in range(*ports): #for every port specified (evaluate tuple)
    t = threading.Thread(target=serve,args=(int(i),)) #new thread for each port (make i an int)
    t.daemon = True #so that Ctrl-C can stop it (ugly, I know)
    t.start() #start the thread
print 'Press Ctrl-C to stop all servers.' #log how to stop
while 1: #then keep the main thread open
    try:
        time.sleep(1) #for termination
    except KeyboardInterrupt: #catch it
        raise SystemExit #raise this instead to make it less ugly
