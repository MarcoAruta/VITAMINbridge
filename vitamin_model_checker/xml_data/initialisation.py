from xml_data.convertion import *

#an attack must be identified by it's id, an is composed of :
#An action
#A set of preconditions that the attacker must possess/know to launch the attack
#A postcondition that is the gain obtained by the attacker once the attack as succeded
class Attack:
    def __init__(self, id, action, preconditions, postcondition):
        self.id = id
        self.action = action
        self.preconditions = preconditions
        self.postcondition = postcondition
        

#take in input an xml file and output the 'mulval' hypergraph associated : the matrix of transition, a list of the attacks and a list of the conditions nodes
def initialisation(file):
    #We get the treated data from the xml
    (transition, node) = build_data(file)
    condition = []
    
    #The transition matrix
    nb_trans = len(transition)
    transition_matrix = [[0 for i in range(nb_trans)] for i in range(nb_trans)]
    for trans in transition:
        #We reduces the indexes by 1, as in the mulval xml it start at 0
        transition_matrix[trans.src - 1][trans.dst - 1] = 1
        
    #the attacks list
    attaques = []
    for noeud in node:
        #AND noes are nodes representing the attacks
        if noeud.type == 'AND':
            #we get the id by decreasing the index of 1. This way we have a correspondance with it's position in the transition matrix
            id = noeud.id
            #we get the post and pre condition with the transition matrix
            for i in range(nb_trans):
                if transition_matrix[id][i] == 1:
                    postcondition = [node[i].fact]
            preconditions = []
            for i in range(nb_trans):
                if transition_matrix[i][id] == 1:
                    preconditions.append(node[i].fact)
            action = node[id].fact
            
            attaques.append(Attack(id, action, preconditions, postcondition))
        else : 
            #other nodes are condition and caracterised only by the knowledge they represent
            condition.append(noeud)
            
    return (transition_matrix, attaques, condition)
            
    
        
    
