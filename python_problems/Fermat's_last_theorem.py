'''from compiler.ast import flatten
import math
def fermat(a,b,c,n):
    z,x,v=[],[],[]
    z=(i for i in range(a))
    x.append([i for i in range(b)])
    v.append([i for i in range(c)])
    for i in flatten(z):
        for j in flatten(x):
            for k in range(10):
                pow
    
   '''
def foo(limit=100):
    for i in range(limit):
        yield i

for i in [10, 100, 500, 1000]:
    a=foo(i)
    b=foo(i)
    c=foo(i)
    d=foo(i)
    # print a,b,c,d
    # print a.next(),b.next(),c.next(),d.next()
    # print a.next(),b.next(),c.next(),d.next()
    import time 
    start = time.time()
    for _a in a:
        b=foo()
        for _b in b:
            c=foo()
            for _c in c:
                d=foo()
                for _d in d:
                    #print _a, _b, _c, _d
                    pass
    print("For i=", i, start,time.time(), "Generator")
    
    start = time.time()
    
    for _a in range(i):
        for _b in range(i):
            for _c in range(i):
                for _d in range(i):
                    pass
    
    print("For i=", i, start,time.time())