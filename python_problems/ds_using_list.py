#This is my shopping List
shoplist=['apple','banana','grapes']
print "I have ",len(shoplist)," items to purchase"
print "The items to be purchased are as follows:"
for items in shoplist:
    print items,
    
print "I also have Pine-Apple to purchase:"
shoplist.append("Pine-apple")
for items in shoplist:
    print items,
print shoplist
print "I will sort my list now"
shoplist.sort()
print shoplist