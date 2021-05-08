def reverse(text):
    return text[::-1]

def is_palindrome(text):
    return text==reverse(text)

something=raw_input("Enter the value:")
if is_palindrome(something):
    print "It is Plaindrome"
else:
    print "It is not palindrome"
