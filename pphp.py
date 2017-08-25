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
