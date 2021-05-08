def foo():
    def inner(loop_, char='', times=8, sep='+'):
        for s in range(loop_):
            print char * times,
            print sep,
        
    l=['+','-','|']
    print l[0],
    for a in range(2):
        inner(2, l[1], 8, l[0])

        print ''
        for k in range(4):
            for s in range(2):
                print l[2],
                print ' ' * 8,
            print l[2]
        print l[0],

    inner(2, l[1], 8, l[0])
        
foo()


'''Output--> A grid


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
'''