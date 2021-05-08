import sys
def factorial(n):
    print len(sys.argv)
    if n==0:
        return 1
    else:
        return n*factorial(n-1)
    
x=factorial(12)
print x