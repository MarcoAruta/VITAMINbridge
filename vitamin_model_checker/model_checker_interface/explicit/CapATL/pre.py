from vitamin_model_checker.model_checker_interface.explicit.CapATL.CapATL import *

# returns possible actions given a set of capacities i.e. [('c','c','c1'),('c', 'c', 'c2')]
# it can corresponds to a knowledge delta
def get_actions_from_capacity_set(capacity_set) :
    result = []
    a = []
    for elem in capacity_set :
        for cap in elem :
            a.append(get_actions_from_capacity(cap))
        a = trouver_combinaisons(a)
        for x in a : 
            if x not in result :
                result.append(x)
        a = []
    return result


def group_by_state(succ_w):
    states = []
    interm = []
    ajout = []
    intermediaire_state = 0
    for success in succ_w :
        intermediaire_state = getattr(success, 'state')
        if intermediaire_state in states :
            for elem in interm :
                if elem[0] == intermediaire_state :
                    elem.append(success)
        if intermediaire_state not in states :
            states.append(intermediaire_state)
            ajout = [intermediaire_state, success]
            interm.append(ajout)
# interm is a list of succ group by their state 
# i.e. [[q1, succ1, succ2],[q3, succ1, succ2]]
    return interm


def action_elem12(elem1, elem2) :
    know_1 = elem1.knowledge
    know_2 = elem2.knowledge
    if tuple(elem1.state) != elem2.state :
        return False
    
    for j1, j2 in enumerate(know_1) :
        for q in j2 :
            if q not in know_2[j1] :
                return False 
    return elem2.action


def action_in_W2(elem, W) :
    result = []
    for a in W :
        if action_elem12(elem, a) != False : 
            result.append(action_elem12(elem, a))
    return result


# returns the intersection of actions i.e. to check if for a state q, unique couple state action
def intersection_same_q(group_by_elmt, W) :
    act = []
    result = []

    for elem in group_by_elmt[1:] :
        if action_in_W2(elem, W) != [] :
            act.append(action_in_W2(elem, W))
    for i in act :
        for j in i : 
            if j not in result :
                result.append(j)
    return result



def unique_state_action_couple(succw,W):
    w_succ = succw
    group = group_by_state(w_succ)
    for elem in group :
        if (len(intersection_same_q(elem,W))) != 1 :
            return False 
    return True


# returns if w=[q,delta1,...,deltak] is in W i.e. there existe an action beta' such that 
# [q,delta1,...,deltak, beta'] is in W
def elem_in_W(w, W) :
    result = []
    interm = []
    k = 0
    for value in W :
        interm = [ x for x in getattr(value, 'knowledge') if x not in getattr(w, 'knowledge')]
        if len(interm)==0 and getattr(value, 'state') == getattr(w, 'state'):
            k += 1
            result.append(value)
    if k == 0 :
        return None 
    return result


def succ_in_W(succw,W, dict_W) :
    
    k = 0 
    succ_w = succw

    l = len(succ_w)
    if l ==0 : 
        return False
    if succ_w == None :
        print("pb succ")
        return False
    for elem in succ_w :
        key_interm = (tuple(elem.state), (elem.knowledge))

        if key_interm not in dict_W : 
            return False
    return True 


def pre(W,coal_Y):
    P = []
    omega_Y = Omega_Y(coal_Y)
    dict_W = {}
    for j in W : 
        key = (j.state, j.knowledge)
        dict_W[key] = j
    for j in omega_Y :
        j1 = succ(j)
        if succ_in_W(j1,W, dict_W) and unique_state_action_couple(j1,W) :
            if j not in P :
                P.append(j)
    return P



