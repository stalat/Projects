x=50
def func(x):
    print 'x is ',x
    x=2
    print "x changed to local ",x
    
    
func(x)
print 'x is ',x
