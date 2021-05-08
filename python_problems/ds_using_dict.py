ab={"abc":"pqr","def":"stu","ghi":"vw","jkl":"xyz"}
print ab
print "The adress is:",ab["abc"]
print ab.values()
print ab.keys()
print ab.items()
print "There are %d items in this list"%(len(ab))
print "The adress of %s is %s"%(ab.keys()[0],ab["abc"])
print "There are {0} members in this dictinonary".format(len(ab),5)


# The same thing they are doing i.e. format and %
for name, adress in ab.items():
    print "{0} and {1}".format(name, adress)
for name, adress in ab.items():
    print "%s with %s"%(name, adress)
