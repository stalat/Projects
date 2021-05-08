def palindrome(string):
    dup=string[::-1]
    if dup==string:
        print "Palindrome"
    else:
        print "Not Palindrome"
        
palindrome("talat")