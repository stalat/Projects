
from operator import itemgetter
def foo(l):
	z=[]
	print "The actual unsorted recieved data is:\n", l
	res1,res2,z,m,x,t=[],[],[],[],[],[]
	for i in range(len(l)):
		z.append(l[i].values())
	t.append(l[0].keys())
	print "You have ",len(t[0]),"number of keys i.e.",t
	c=raw_input("You want to sort the data on which Key Basis: ")
	if c in l[0].keys():
		print "You are getting processed:"
	else:
		print "The key selected is not present in the KeyList"	
	
	for i in sorted(z):
		m.append(tuple(i))
	if c in t[0]:
		print "You have selected",c,"as your key"
		for i in sorted(m,key = itemgetter(t[0].index(c))):
			res1=[]
			res1=dict(zip(tuple(l[0].keys()),tuple(i)))
			res2.append(res1)
		print "\nThe List of Dictionaries based on sorted",c,"keys is as Follows:\n",res2



		
if __name__=="__main()__":
	foo()


"""
where l=[{'id': 4, 'name': 'Talat'}, {'id': 2, 'name': 'Saurabh'}, {'id': 1, 'name': 'Bhuvi'}, {'id': 3, 'name': 'Vishnu'}]

or we can use as    from operator import itemgetter
sorted(l,key=itemgetter('id'/'name'))"""

