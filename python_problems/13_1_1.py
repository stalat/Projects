import string
def is_reverse(text):
    return text[::-1]
def is_palindrome(text):
    return text==is_reverse(text)

something=raw_input("Enter some string with Puctuations: ")
p=(string.punctuation)
l=(string.letters)
c=chr(32)
#exclusion of Space and Punctuation marks from the string
something_new="".join([x for x in ("".join([s for s in something if s not in p])) if x not in c])
print something_new
print p
print l
if is_palindrome(something_new):
    print "The string is palindrome"
else:
    print "The string is not palindrome"