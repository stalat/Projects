import sys
global x
def foo():
    x=0
    print "Hello"
    x+=1
    if x<5:
        foo1()
    else:
        sys.exit()
    
def foo1():
    print "Hi"
    foo()
    
if __name__=="__main__":
    foo()