# defaultdict


from collections import defaultdict

def default_value() :
    return 0

# char_count = {}
char_count = defaultdict( default_value )
string = "aaaabvbbbkhkafjkafdsjvk;zcvm;adsfhjasfasdl;kfa"

for c in string:
    char_count[c] += 1

print( char_count )










