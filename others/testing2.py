from fuzzywuzzy import fuzz, process

s2 = "I am lovee you"
s1 = "I love you too so much"

print(fuzz.partial_ratio(s1, s2))