class Parent:
    def mymethod(self):
        print "This method is of Parent class"
        print "The instance is: ",isinstance(b,Parent)
        
class Child(Parent,object):
    def mymethod(self):
        print "This method is of Chils Class"
        print "This is Corect code"
        print issubclass(Child,Parent)
        print "The instance is: ",isinstance(b,Child)

b=Child()
b.mymethod()
a=Parent()
a.mymethod()

