from xml_data.to_cgs import *

#From an input file (.xml), a file of deactivable condition and a list of goals conditions this function output in the file "file" the txt file that will allow VITAMIN to compute and check the properties we need.
def writting(input, file, file_cond, Objectif_attaque):
    #result transition is of no use, but can serve in net improvments of the program
    (result_state, result_transition) = to_cgs(input, file_cond)
    fichier = open(file+"_Vitamin.txt", "w")
    fichier.write("Transition_With_Costs")
    fichier.close()
    #We write the transitions
    taille = len(result_state)
    #with one line by state
    for i in range(taille):
        transition = ""
        for j in range(taille):
            #If there is no indication then there is no transition
            if j >= len(result_state[i][2]):
                transition += "0 "
                #if the transition is positive then it's deactivable. Otherwise we put it at a maximum : the defenders would need to be omnipotent to deactivate it
            elif result_state[i][2][j] > 0:
                transition += "1 "
            elif result_state[i][2][j] < 0:
                transition += str(taille) + " "
            else:
                transition += "0 "
        fichier = open(file+"_Vitamin.txt", "a")
        fichier.write("\n" + transition)
        fichier.close()         
    
    #We name the different state in the order we write them
    fichier = open(file+"_Vitamin.txt", "a")
    fichier.write("\nName_State")
    fichier.write("\n")
    for i in range(taille):
        fichier.write(str(i) +" ")
    fichier.close()
    
    #there is one atomic proposition : the attacker win
    fichier = open(file+"_Vitamin.txt", "a")
    fichier.write("\nAtomic_propositions")
    fichier.write("\nA_w")
    fichier.close()
   
    #We look with the files of goals for the attacker teh states on which he win
    fichier = open(file+"_Vitamin.txt", "a")
    fichier.write("\nLabelling")
    for i in result_state:
        gagne = 0
        for cond in Objectif_attaque:
            if cond in i[1]:
                gagne = 1
        #if the attacker win then the defender lose.
        fichier.write("\n" + str(1 - gagne) + " " + str(gagne))
    fichier.close()
    
    fichier = open(file+"_Vitamin.txt", "a")
    fichier.write("\nNumber_of_agents")
    fichier.write("\n2")
    fichier.close()
    

writting("./xml_data/test.xml", "./xml_data/test_output", "./xml_data/cond.txt", ['Cond 4'])