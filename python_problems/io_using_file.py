poem="""\
programming is fun
when the work is done 
if you wanna make your work as fun
do the code in python"""


f=open("poem.txt",'w+')
f.write(poem)
f.close()
f=open("poem.txt")

while True:
    l=f.readlines()
    print l
f.close()
        
