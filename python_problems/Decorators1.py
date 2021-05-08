def outer(foo):
	print "This is Decorator"
	ret=foo()
	print ret






@outer
def foo():
	return "Yes, It is a Positive Integer NUmber"

if __name__=="__main()__":
	foo()
