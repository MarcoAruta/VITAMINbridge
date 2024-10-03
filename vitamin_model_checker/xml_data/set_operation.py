# allow to see if all the eements of a list a are in a list b
def into(lista, listb):
    for i in range(len(lista)):
        temp = False
        for j in range(len(listb)):
            if lista[i] == listb[j]:
                temp = True
        if temp == False:
            return False
    return True 