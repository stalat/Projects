class Robot:
    
    popullation=0
    def __init__(self,Name):
        """Ths is a class and having the concepts of The Object Oriented Programming"""
        self.Name=Name
        print "Initializing {0}".format(self.Name)
        Robot.popullation+=1
        print self.popullation
    def die(self,age):
        """I am Dying"""
        print "{0} is going to be destroyed @age of {1}".format(self.Name,age)
        Robot.popullation-=1
        if Robot.popullation==0:
            print "{0} was the Last robot that's been destroyed".format(self.Name)
        else:
            print "We have {0} number of Robots remaining".format(Robot.popullation)
    def No_of_robots_available(self):
        print "The total number of the robots, we have is: ",Robot.popullation
    def Robot_detail(self):
        print "The detail of the robot is: ",self.Name
        
        
        
r1=Robot("Talat Parwez")
r2=Robot("Talat Parwez1")
r1.No_of_robots_available()
r2.Robot_detail()
Robot.__doc__