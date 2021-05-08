class myDecorator(object):
    def __init__(self,f):
        print "Inside myDecorator.__init__()"
        f() #Prove that function definition has completed
    def __call__(self):
        print "Inside myDecorator.__call__()"

        
     
@myDecorator
def aFunction():
    print "Inside aFunction()"
    
print "Finished decorating aFunction"

aFunction()