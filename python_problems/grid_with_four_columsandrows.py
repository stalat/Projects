x='+{0}+{0}+{0}+{0}+'
y='|{0}|{0}|{0}|{0}|'

print x.format('-'*5)
for i in range(4):
    for i in range(3):
        print y.format('*'*5)
    print x.format('-'*5)
