class Person:
    def __init__(self,name):
        self.name=name
    def say_hi(self):
        print "Hello, My Name is: ",self.name
        
p=Person('Talat Parwez')
p.say_hi()