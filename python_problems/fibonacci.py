def fibonacci(n):
    a,b=0,1
    print a
    print b
    for i in range(n):
        c=a+b
        a,b=b,c
        print c
    
fibonacci(8)
________________________________________________________________________
def fibonacci(n):
    if n==0:
        return 0
    elif n==1:
        return 1
    else:
        return fibonacci(n-1)+fibonacci(n-2)

print fibonacci(8)
