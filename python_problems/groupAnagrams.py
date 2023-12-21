"""
def groupAnagrams(words):
	resultant_list = list()
	for idx, i in enumerate(words):
		intermitent_list = list()
		for jdx, jj in enumerate(words[idx+1: ]):
			if sorted(i) == sorted(jj):
				intermitent_list.append(i)
				intermitent_list.append(jj)
		intermitent_list = list(set(intermitent_list))
		resultant_list.append(intermitent_list)
	return [i for i in filter(lambda x:x, resultant_list)]
	"""

"""def groupAnagrams(words):
    anagrams = dict()
    for word in words:
        sortedWord = "".join(sorted(word))
        if sortedWord in anagrams:
            anagrams[sortedWord].append(word)
        else:
            anagrams[sortedWord] = [word]
    return list(anagrams.values())
				
				
print(groupAnagrams(["yo", "act", "flop", "tac", "foo", "cat", "oy", "olfp"]))
"""

"""def twoNumberSum(array, targetSum):
    # Create a dictionary, make every number as key
    # Now try adding new number to it, If they results to targetSum, then return those
    # two numbers else return empty array
    num_dictionary = dict()
    for number in array:
        if number not in num_dictionary:
            num_dictionary[number] = [number]
            for existing_number in num_dictionary:
                if number + existing_number == targetSum and number != existing_number:
                    return [number, existing_number]
    return []"""

"""
def twoNumberSum(array, targetSum):
    # Create a dictionary, make every number as key
    # Now try adding new number to it, If they results to targetSum, then return those
    # two numbers else return empty array
    num_dictionary = dict()
    for num in array:
        potential_sum = targetSum - num
        if potential_sum in num_dictionary:
            return [num, potential_sum]
        else:
            num_dictionary[num] = True
    return []     
        
print(twoNumberSum(array=[3, 5, -4, 8, 11, 1, -1, 6], targetSum=10))
"""