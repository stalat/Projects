class SuperParent(object):
    def __init__(self,name,age,adress):
        self.name=name
        self.age=age
        self.adress=adress
        print "The name,age and adress of Individual is:",name,age,adress
    def tell(self):
        print 'Name:"{0}" Age:"{1}" Adress:"{2}"'.format(self.name, self.age,self.adress)

        
class Teacher(SuperParent):
    def __init__(self,name,age,adress,subject,salary):
        SuperParent.__init__(self,name,age,adress)
        self.subject=subject
        self.salary=salary
    def tell(self):
        SuperParent.tell(self)
        print "salary is: ",self.salary


        
A=Teacher("Talat Parwez",22,"BTM",300000,"Computer Networks")
A.tell()
