import sys

      
_templx = '+{0}+{0}+'
_temply = '|{0}|{0}|'

def foo1():
    print _templx.format('-'*10)
    foo(3)
    
def foo(n=3):
    if n>=0:
        for i in range(5):
            print _temply.format(' '*10)
        print _templx.format('-'*10)
        foo(n-1)
        
foo1()