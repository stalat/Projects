def foo():
    l=['+','-','|']
    for i in range(1):
        print l[0],
        for a in range(2):
            for f in range(2):
                for j in range(4):
                    print l[1],
                print l[0],
            print ''
            for k in range(4):
                for s in range(2):
                    print l[2],
                    for m in range(4):
                        print ' ',
                print l[2]
            print l[0],
        for d in range(2):
            for j in range(4):
                print l[1],
            print l[0],
        
foo()


Output--> A grid


+ - - - - + - - - - + 
|         |         |
|         |         |
|         |         |
|         |         |
+ - - - - + - - - - + 
|         |         |
|         |         |
|         |         |
|         |         |
+ - - - - + - - - - +
