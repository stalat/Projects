class Parent:
    ParentAttr=100
    def __init__(self):
        print "Calling parent constructor"
    def parentMethod(self):
        print "Calling Parent Method"
    def setAttr(self,attr):
        Parent.ParentAttr=attr
    def getAttr(self):
        print "The attribute value is: ",Parent.ParentAttr
class Child(Parent):
    def __init__(self):
        print "Calling child constructor"
    def childMethod(self):
        print "Calling Child Method"
        
a=Child()
a.childMethod()
b=Parent()
b.parentMethod()
a.setAttr(2500)
a.getAttr()

