import re, sys, json, os, traceback, cgi, urlparse #we use a lot of stuff
from cStringIO import StringIO #for convenience

def touch(fi): #function to create db if needed
    with open(fi, 'w') as f: #open the file
        f.write('{}') #make it an empty json object
eu = lambda p: os.path.abspath(os.path.expandvars(os.path.expanduser(p))) #expand variables and user dirs
if os.name == 'posix': #if we're on UNIX-like oses (inc Mac)
    if not '.pphp' in os.listdir(eu('~')): #if the config directory doesn't even exist
        os.mkdir(eu('~/.pphp')) #make the directory
        touch(eu('~/.pphp/__DATABASE__.json')) #touch the db
    else:
        if not '__DATABASE__.json' in os.listdir(eu('~/.pphp')): #if the dir is there but the file isn't
            touch(eu('~/.pphp/__DATABASE__.json')) #touch the db
    dbname = eu('~/.pphp/__DATABASE__.json') #evaluate database name
elif os.name in ['nt', 'ce', 'os2']: #if we're on Windows (most variants)
    if not '.pphp' in os.listdir(eu('%appdata%')): #if the dir doesn't exist
        os.mkdir(eu('%appdata%/.pphp')) #and so on
        touch(eu('%appdata%/.pphp/__DATABASE__.json'))
    else:
        if not '__DATABASE__.json' in os.listdir(eu('%appdata%/.pphp')):
            touch(eu('%appdata%/.pphp/__DATABASE__.json'))
    dbname = eu('%appdata%/.pphp/__DATABASE__.json')
else: #if we can't even tell what we're on
    raise OSError('Unsupported operating system') #raise that

__all__ = ['do'] #define that this is the only thing we want to import for "from pphp import *"

def do(html, server=None):
    #setup
    if server:
        if not '.pphp-config' in os.listdir(server.root): #if the config file isn't present
            try: key = sys.argv[3] #get db key from arg
            except IndexError: print('For a first run, please specify a database key in the third argument. Quitting...'); sys.exit()
            with open(server.root+'/.pphp-config', 'w') as f: #write the key to the config file
                f.write(key)
        else: #if the config file is present
            with open(server.root+'/.pphp-config', 'r') as f: #get the key from the file
                key = f.read().strip()
        _GET=urlparse.parse_qs(urlparse.urlparse(server.path).query, keep_blank_values=1) #get data
        if server.command == 'POST': #if this is POST
            ctype, pdict = cgi.parse_header(server.headers.getheader('content-type')) #parse post headers
            if ctype == 'multipart/form-data': #if this is multipart form data
                _POST = cgi.parse_multipart(server.rfile, pdict) #parse data
            elif ctype == 'application/x-www-form-urlencoded': #if this is application form data
                length = int(server.headers.getheader('content-length')) #get length of data
                _POST = cgi.parse_qs(server.rfile.read(length), keep_blank_values=1) #read length bytes of data (all the bytes)
            else: #not recognized or not there
                _POST = {} #empty post data
        else: _POST = {} #it's not post, just make that empty
        for k, v in _GET.items():
            del _GET[k]
            if type(v) == list:
                _GET[cgi.escape(k)] = [cgi.escape(sv) for sv in v]
            else:
                _GET[cgi.escape(k)] = cgi.escape(v)
        for k, v in _POST.items():
            del _POST[k]
            if type(v) == list:
                _POST[cgi.escape(k)] = [cgi.escape(sv) for sv in v]
            else:
                _POST[cgi.escape(k)] = cgi.escape(v)
        _REQUEST=dict(_GET, **_POST) #join the two together
        path = urlparse.urlparse(server.path) #parsed path
        _SERVER={'PPHP_SELF': path.path, #path to file
                 'GATEWAY_INTERFACE': cgi.__version__, #inconsistent with PHP
                 'SERVER_ADDR': server.server.server_address[0], #server address
                 'SERVER_NAME': server.server.server_name, #server name
                 'SERVER_SOFTWARE': 'PPHP/3.0', #custom :)
                 'SERVER_PROTOCOL': server.protocol_version, #server protocol version
                 'REQUEST_METHOD': server.command, #request method
                 'QUERY_STRING': path.query, #query string
                 'REMOTE_ADDR': server.client_address[0], #client address
                 'REMOTE_PORT': server.client_address[1], #client port
                 'SERVER_PORT': server.server.server_address[1], #server port
                 'SCRIPT_FILENAME': os.path.abspath(server.root+path.path), #absolute path to file
                 'PATH_TRANSLATED': os.path.realpath(os.path.abspath(server.root+path.path)) #translated path to file
                 } #whoo
    __scripts__ = re.findall(r'<\?pphp.*?\?>', html, re.DOTALL) #get all the scripts
    __outputs__ = [] #outputs
    if server:
        with open(dbname, 'r') as f: #get database
            __FULLDB__ = json.loads(f.read().strip()) #load json from file into py dict
            try: __db__ = __FULLDB__[key] #try to get the database for this key
            except KeyError: #wait what
                __FULLDB__[key] = {} #oh we don't have a db here
                __db__ = {} #make it ^^
    __pre__ = sys.stdout #to get around a weird UnboundLocalError
    for __script__ in __scripts__: #for every script
        __pre__ = sys.stdout #backup of sys.stdout so that we can restore it later
        sys.stdout = StringIO() #replace stdout with something we can use to capture stdout
        echo = sys.stdout.write #define keyword echo
        escape = cgi.escape
        try: exec __script__[7:-2] #execute code (without the tag)
        except: #an error ocurred, what now?
            sys.stdout.close() #close the StringIO
            sys.stdout = __pre__ #restore normal stdout
            html = '<!doctype html><head><title>Error</title><style>* {color:red} div {font-family:monospace}</style></head><body><h1>Exception happened during processing of code</h1><div>' #starter for error
            trace = traceback.format_exc().split('\n') #get traceback
            for i in trace: #for every line
                html += cgi.escape(i).replace(' ', '&nbsp;')+'<br/>' #add it
            html += '</div></body></html>' #close
            return html #return finished error
        __output__ = sys.stdout.getvalue() #get stdout value
        sys.stdout.close() #close for completeness
        sys.stdout = __pre__ #restore original stdout
        __outputs__.append(__output__) #store the output
    for out in __outputs__: #for every output
        html = re.sub(r'<\?pphp.*?\?>', str(out), html, count=1, flags=re.DOTALL) #replace each script with its output
    if server:
        __FULLDB__[key] = __db__ #update full db
        with open(dbname, 'w') as f: #open the db
            f.write(json.dumps(__FULLDB__)) #update the file
    sys.stdout = __pre__ #restore stdout
    return html #return finished html

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print('Usage: python -m pphp <root directory for server> <IP> [db key if this is the first run for this root]')
        sys.exit(1)
    try: from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler #py2
    except ImportError: from http.server import HTTPServer, BaseHTTPRequestHandler #py3
    import threading, time #necessary
    try: import thread #py2
    except ImportError: import _thread as thread #py3

    class handler(BaseHTTPRequestHandler): #request handler
        root = sys.argv[1].strip('"') #get the path from arg
        root = os.path.abspath(eu(root))
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
                self.wfile.write(do(f.read(), self)) #pass raw html and server state and get processed html
                f.close() #close for completeness
            except IOError: #file not found
                self.send_error(404) #send not found error
                self.end_headers() #end headers
        def do_POST(self): #post requests
            try:
                pth = urlparse.urlparse(self.path) #path object
                path = pth.path #path string without anything else
                path = self.indexify(path) #and so on
                if path is None:
                        raise IOError
                f = open(path)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(do(f.read(), self))
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

    addr, ports = sys.argv[2].strip('"').split(':') #format is IP:(portmin, portmax[, portstep])
    ports = eval(ports) #evaluate tuple
    if type(ports) == int: #wait it was int?
        ports = (ports, ports+1) #make it a tuple
    assert type(ports) == tuple, "expected tuple or int, got " + type(ports).__name__ #if it wasn't tuple or int, catch that

    serving_ports = [] #ports being served

    def serve(port): #function to serve one port
        global lock, addr, serving_ports #lock object needs to be global; address needs to be consistent; port list needs to be global
        with lock: #synced start
            httpd = HTTPServer((addr, port), handler) #start the server
            print('Serving %s on port %s...' % httpd.server_address) #log starting server
        while port in serving_ports: #while we're serving this port
            httpd.handle_request() #handle one request
        with lock: #synced stop
            print('Stopping server on %s:%s...' % httpd.server_address) #log stopping server

    def control(): #console control
        global serving_ports #port list needs to be global
        while serving_ports: #while there are ports being served
            i = int(raw_input('Enter port number to stop: ')) #get port number
            try: #try to remove it from the list
                i = serving_ports.index(i)
                serving_ports.pop(i)
            except ValueError: #do nothing if it's not there
                pass
        print('Stopped all servers') #no more servers

    for i in range(*ports): #for every port specified (evaluate tuple)
        thread.start_new_thread(serve,(int(i),)) #new thread for each port (make i an int)
        serving_ports.append(int(i)) #add port number to ports being served

    thread.start_new_thread(control,()) #start control as well
    while serving_ports: #keep the main thread alive while there are ports being served
        time.sleep(1)
