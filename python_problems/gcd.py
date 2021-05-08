import random
class A():
    '''Calculating the Gdc of Parameters passed to the function'''
    def __init__(self,a,b):
        self.a=a
        self.b=b
        print "self",self.a
        print "self",self.b
    def equal(self,a,b):
        if a<b:
            while a<b:
                a+=self.a
        if b<a:
            while b<a:
                b+=self.b
        if a==b:
            print "The Greatest common divisor is: ",b
        else:
            self.equal(a,b)
            
i,j=int(10*(random.random())),int(10*(random.random()))
obj=A(i,j)
obj.equal(i,j)