import bottle
import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer
@bottle.route('/')
@bottle.route('/index.html')
def foo():
	return "<h1>This is my First Bottle Proram</h1>"
	hostname="localhost"
	
	poo(hostname=hostname,port=8085)

def poo(**kwargs):
	print kwargs
	XmlRpc.server(**kwargs)
	bottle.run(host=hostname, port=8085, reloader=True)

class XmlRpc(object):
	def server(self,**kwargs):
		hostname=kwargs.get("hostname")
		port=kwargs.get("port")
		if not hostname:
            raise Exception("Expecting value for keyword argument hostname")
        if not port:
            raise Exception("Expecting value for keyword argument port")
		server = SimpleXMLRPCServer((hostname, port))
		print "\n>>> Listening on port {0}...\n".format(port)
		server.serve_forever()



