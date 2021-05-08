"""This is using the CSV MODULE """
import csv
import datetime
import sys
import glob

K,t,time_difference=[],[],[]
with open(sys.argv[1],'rt') as f:
    reader=csv.reader(f)
    for row in reader:
        if len(row)==4:
            continue
        else:
            #print row
            K.append(row[0])
for i in K:
    t.append(datetime.datetime.strptime(i,"%H:%M:%S"))
print len(t)
for idx,item in enumerate(t):
    #print item+datetime.timedelta(hours=12)
    if item==t[0]:
        print "First Item"
        continue
    elif t[idx-1]>t[idx]:
        d=(t[idx]+datetime.timedelta(hours=12))-t[idx-1]
        id=idx-1
    else:
        time_difference.append(t[idx]-t[idx-1])
time_difference.insert(id,d)
print time_difference
for i in time_difference:
    print i

"""It will print the output from 1 input file to another output file """
with open(sys.argv[1],'r') as csvinput:
    with open("output.csv", 'w') as csvoutput:
        writer = csv.writer(csvoutput, lineterminator='\n')
        reader = csv.reader(csvinput)
        all = []
        row = next(reader)
        all.append(row)
        #for m in time_difference:
        #    print m
        m = iter(time_difference)
        try:
            for row in reader:
                row.append(m.next())
                all.append(row)
        except:
            pass
        writer.writerows(all)
