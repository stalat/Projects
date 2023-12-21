def self_writing():
	f=open("self_writing.py")
	t=f.read()
	print(t)
	f.close()

if __name__=='__main__':
	self_writing()
