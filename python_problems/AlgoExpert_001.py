def sum(arr):
    sum = 0
    for item in arr:
        sum += item

sum([1,2,3,4,5,6,6,7,8])

def pair(arr):
    for i in arr:
        for j in arr:
            print(i, j)

pair([1,2,3])
