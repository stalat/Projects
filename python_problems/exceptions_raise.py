class shortInputException(Exception):
    def __init__(self,length,atleast):
        self.length=length
        self.atleast=atleast
        try:
            text=raw_input("Enter a string: ")
            if len(text)<3:
                raise shortInputException(len(text),3)
        except EOFError:
            print "You may have pressed Ctrl+D"
        except shortInputException as ex:
            print "You're not fulfilling the requirements"
        else:
            print "No exceptions were raised for this process"

a=shortInputException(3,3)