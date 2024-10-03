from xml_data.initialisation import *
from xml_data.set_operation import *

#To suppress the space in a string, for vitamin interpretation
def suppr_space(string):
    res = ""
    for caracter in string:
        if caracter == " ":
            res += "_"
        else:
            res += caracter
    return res
            
            
#Get the lines in a file and put them in an array
def recupere_cond (file_cond):
    fichier = open(file_cond, "r")
    res = [line.rstrip('\n') for line in fichier]
    fichier.close()
    return (res)
    
            

#This program take in entry an xml file describing an hypergraph and a file with the conditions that can be temporarly deactivated and output a cgs structure : states and there transitions
            
def to_cgs(file, file_cond):
    #We get the list of all the conditions that can be temporarly deactevated
    cond_deactiv = recupere_cond(file_cond)
    #We get the data on the hypergraph computed from the xml
    (matrix, attacks, condition) = initialisation(file)
    nb_state_graph = len(matrix)
    nb_condition = len(condition)
    initial_state_flag = [1 for i in range(nb_condition)]
    for i in range(nb_condition):
        #We look in all states : a state without previous condition will be part of the initial state of the cgs
        for j in range(nb_state_graph):
            if matrix[j][condition[i].id]:
                initial_state_flag[i] = 0
    #each state will be composed of : id, conditions, list of successors
    initial_state = (0, [], [])
    for i in range(len(initial_state_flag)):
        if initial_state_flag[i]:
            initial_state[1].append(condition[i].fact)
    initial_state[2].append(0)
    #State array will contains all state that have been fully taken in account (studied each attacks)
    state_array = []
    #transition array will contains the transition swith the full name of : preconditions, postconditions and the attack name
    #It is not useful here but can be of interest for next improvments
    transition_array = []
    #we initiate the list of state to take in account with the initial state
    left_states = [initial_state]
    #this variable will be equal to the number of states added in left_states and so their id (we then start with id  for the initial state)
    nb_states = 0
    #we take in account all the states
    while left_states != []:
        current_state = left_states[0]
        del left_states[0]
        #we take in account all the attacks fo each states
        for attaque in attacks:
            #checking if the attack can be launch from the state
            if  (not into(attaque.postcondition, current_state[1])) and into(attaque.preconditions, current_state[1]):
                new_conditions = []
                for cond in current_state[1]:
                    new_conditions.append(cond)
                new_state = (nb_states + 1, new_conditions, [])
                new_state[1].append(attaque.postcondition[0])
                #we build is transition list from what we know : he doesn't lead to any of the previous states previously added in the left_state flag
                #Otherwise, it would have been already taken into account
                for i in range(nb_states):
                    new_state[2].append(0)
                new_state[2].append(0)
                #We now check if the state already exist
                already_exist = 0
                #we look in the state already taken in account
                for old_state in state_array:
                    #a state is characterisez by it's first list : the conditions that are know by the attacker on it
                    if into(new_state[1], old_state[1]) and into(old_state[1], new_state[1]):
                        #we add the transition in the origin state, to avoid forgeting transitions
                        transition_array.append((suppr_space(attaque.action), current_state, old_state)) 
                        #we then update the transition list of the old state
                        while len(current_state[2]) < old_state[0] + 1:
                            current_state[2].append(0)
                        #we look if the attack can be deactivated
                        deactivable = 0
                        for precond in attaque.preconditions:
                            if precond in cond_deactiv:
                                #if the attack is deactivable, deactivable will be 2
                                deactivable = deactivable + 2 - deactivable
                        current_state[2][old_state[0]] = -1 + deactivable #1 if it's deactivable, -1 otherwise  
                        already_exist += 1
                if already_exist == 0:
                    #we do the same with the states present in left_states
                    for old_state in left_states:
                        if into(new_state[1], old_state[1]) and into(old_state[1], new_state[1]):
                            transition_array.append((suppr_space(attaque.action), current_state, old_state)) 
                            while len(current_state[2]) < old_state[0] + 1:
                                current_state[2].append(0)
                            #we look if the attack can be deactivated
                            deactivable = 0
                            for precond in attaque.preconditions:
                                if precond in cond_deactiv:
                                    #if the attack is deactivable, deactivable will be 2
                                    deactivable = deactivable + 2 - deactivable
                            current_state[2][old_state[0]] = -1 + deactivable #1 if it's deactivable, -1 otherwise
                            already_exist += 1
                #if it pass the test, then it's a new state and we will add it to the list of state which are to be taken in account
                if already_exist == 0:
                    left_states.append(new_state)
                    transition_array.append((suppr_space(attaque.action), current_state, new_state))     
                    while len(current_state[2]) < nb_states + len(left_states) + 1:
                        current_state[2].append(0)
                    #we look if the attack can be deactivated
                    deactivable = 0
                    for precond in attaque.preconditions:
                        if precond in cond_deactiv:
                            #if the attack is deactivable, deactivable will be 2
                            deactivable = deactivable + 2 - deactivable
                    current_state[2][new_state[0]] = -1 + deactivable #1 if it's deactivable, -1 otherwise
                    nb_states += 1               
        state_array.append(current_state)        
 
    return (state_array, transition_array)
    

