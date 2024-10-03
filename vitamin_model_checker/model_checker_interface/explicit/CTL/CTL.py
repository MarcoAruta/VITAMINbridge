from vitamin_model_checker.models.CGS import *
from binarytree import Node
from vitamin_model_checker.logics.CTL import verifyCTL, do_parsingCTL

# returns the states where the proposition holds
def get_states_prop_holds(prop):
    states = set()
    prop_matrix = cgs.get_matrix_proposition()

    index = cgs.get_atom_index(prop)
    if index is None:
        return None
    for state, source in enumerate(prop_matrix):
        if source[int(index)] == 1:
            states.add(state)
            #states.add("s" + str(state))
    return states


# set of states (ex. s1, s2) as input and returns a set of indices to identify them
def convert_state_set(state_set):
    states = set()
    for elem in state_set:
        position = cgs.get_index_by_state_name(elem)
        states.add(int(position))
    return states


# converts a string into a set
def string_to_set(string):
    #print(f"string:{string}")
    if string == 'set()':
        return set()
    set_list = string.strip("{}").split(", ")
    new_string = "{" + ", ".join(set_list) + "}"
    return eval(new_string)


#  function that builds a formula tree, used by the model checker
#This function builds a formula tree, creating nodes for operators and atomic propositions
# Eg: Input: !AXa, Tree Root: NOT operator, Left Child: AXa
def build_tree(tpl):
    if isinstance(tpl, tuple):
        root = Node(tpl[0])
        if len(tpl) > 1:
            left_child = build_tree(tpl[1])
            if left_child is None:
                return None
            root.left = left_child
            if len(tpl) > 2:
                right_child = build_tree(tpl[2])
                if right_child is None:
                    return None
                root.right = right_child
    else:
        states = set()
        states_proposition = get_states_prop_holds(str(tpl))
        if states_proposition is None:
            return None
        else:
            for element in states_proposition:
                states.add(cgs.get_state_name_by_index(element))
            root = Node(str(states))
    return root


# It returns the states predecessors of those held in input
def pre_image_exist(transitions, list_holds_p):
    #print(f"input transitions: {transitions}")
    #print(f"pre-image: here're the input states where prop holds {list_holds_p}")
    pre_list = set()
    for state in list(list_holds_p):
        predecessors = {s for s, t in transitions if t == state}
        #print(f"pre-image predecessors: {predecessors}")
        pre_list.update(predecessors)
    return pre_list

def pre_image_all(transitions, list_holds_p):
    pre_list = set()
    for state in list(list_holds_p):
        predecessors = {s for s, t in transitions if t == state}
        for predecessor in predecessors:
            successor_states = {t for s, t in transitions if s == predecessor}
            if successor_states.issubset(list_holds_p):
                pre_list.add(predecessor)
    return pre_list


#This function solves formula tree returning a result for model checking. It analyzes tree recursively, solving nodes depending on the associated operator.
# Eg: Same build tree formula: !AXa -> this function starts to solve AXa node as first, and then applies NOT at the result.
#To solve AXa node, it uses pre-image function to define the states set where a proposition is satisfied. The result will be assigned to AXa node.
#At the end, the algorithm applies NOT operator at the result for AXa. To do so, it computes the complementary states set for those that satisfy AXa.
# The final result is stored in NOT operator root.
def solve_tree(node):

    if node.left is not None:
        print(f"node left: {node.left}")
        print(type(node.left))
        solve_tree(node.left)


    if node.right is not None:
        print(f"node right: {node.right}")
        solve_tree(node.right)

    if node.right is None:   # UNARY OPERATORS: not, globally, next, eventually
        if verifyCTL('NOT', node.value):  # e.g. ¬φ
            states = string_to_set(node.left.value)
            ris = set(cgs.get_states()) - states
            node.value = str(ris)

        elif verifyCTL('EXIST', node.value) and verifyCTL('GLOBALLY', node.value):  # e.g. EGφ
            states = string_to_set(node.left.value)
            #print(f"states labelled as node lef(states where prop holds): {states}")
            p = set(cgs.get_states())
            t = states
            while p - t:  # p not in t
                p = t
                t = pre_image_exist(cgs.get_edges(), p) & states
            node.value = str(p)

        elif verifyCTL('FORALL', node.value) and verifyCTL('GLOBALLY', node.value):  # not(EF(not p)) e.g. AGφ
            states = string_to_set(node.left.value)
            compl_states = set(cgs.get_states()) - states
            #print(f"states labelled as node lef(states where prop holds): {compl_states}")
            p = set()
            t = compl_states
            while t - p:  # t not in p
                p.update(t)
                t = pre_image_all(cgs.get_edges(), p)
            out = set(cgs.get_states()) - p
            node.value = str(out)

        elif verifyCTL('FORALL', node.value) and verifyCTL('NEXT', node.value):# e.g. EXφ
            states = string_to_set(node.left.value)
            negated_states = set(cgs.get_states()) - states
            #print(f"states labelled as node lef(states where prop holds): {negated_states}")
            ris = pre_image_all(cgs.get_edges(), negated_states)
            complement = set(cgs.get_states()) - ris
            print(f"compl: {complement}")
            node.value = str(complement)

        elif (verifyCTL('EXIST', node.value) and verifyCTL('NEXT', node.value)):
            states = string_to_set(node.left.value)
            #print(f"states labelled as node lef(states where prop holds): {states}")
            ris = pre_image_exist(cgs.get_edges(), states)
            node.value = str(ris)


        elif verifyCTL('EXIST', node.value) and verifyCTL('EVENTUALLY', node.value):  # trueUϕ.
            states = string_to_set(node.left.value)
            #print(f"states labelled as node lef(states where prop holds): {states}")
            p = set()
            t = states
            while t - p:  # t not in p
                p.update(t)
                t = pre_image_exist(cgs.get_edges(), p)
            node.value = str(p)

        elif verifyCTL('FORALL', node.value) and verifyCTL('EVENTUALLY', node.value):  # not (EG(not p))
            states = string_to_set(node.left.value)
            compl_states = set(cgs.get_states()) - states
            #print(f"states labelled as node lef(states where prop holds): {compl_states}")
            p = set(cgs.get_states())
            t = compl_states
            while p - t:  # p not in t
                p = t
                t = pre_image_all(cgs.get_edges(),p) & compl_states
            ris = set(cgs.get_states()) - p
            node.value = str(ris)

    if node.left is not None and node.right is not None:  # BINARY OPERATORS: or, and, until, implies
        if verifyCTL('OR', node.value): # e.g. φ || θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.union(states2)
            node.value = str(ris)


        elif verifyCTL('EXIST', node.value) and verifyCTL('UNTIL', node.value):  # e.g. AφUθ
            states1 = string_to_set(node.left.value)
            #print(f"states labelled as node left(states where prop holds): {states1}")
            states2 = string_to_set(node.right.value)
            #print(f"states labelled as node right(states where prop holds): {states2}")
            p = set()
            t = states2
            while t - p:  # t not in p
                p.update(t)
                t = pre_image_exist(cgs.get_edges(), p) & states1
            node.value = str(p)

        elif verifyCTL('AND', node.value):  # e.g. φ && θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.intersection(states2)
            node.value = str(ris)

        elif verifyCTL('IMPLIES', node.value):  # e.g. φ -> θ
            # p -> q ≡ ¬p ∨ q
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            not_states1 = set(cgs.get_states()).difference(states1)
            ris = not_states1.union(states2)
            node.value = str(ris)

# returns whether the result of model checking is true or false in the initial state
def verify_initial_state(initial_state, string):
    if initial_state in string:
        return True
    return False


# does the parsing of the model, the formula, builds a tree and then it returns the result of model checking
# function called by front_end_CS
def model_checking(formula, filename):
    global cgs

    if not formula.strip():
        result = {'res': 'Error: formula not entered', 'initial_state': ''}
        return result

    # model parsing
    cgs = CGS()
    cgs.read_file(filename)

    # formula parsing
    print(f"formula to parse: {formula}")
    res_parsing = do_parsingCTL(formula)
    if res_parsing is None:
        result = {'res': "Syntax Error", 'initial_state': ''}
        return result
    root = build_tree(res_parsing)
    if root is None:
        result = {'res': "Syntax Error: the atom does not exist", 'initial_state': ''}
        return result
    print(f"root is: {root}")
    # model checking
    solve_tree(root)

    # solution
    initial_state = cgs.get_initial_state()
    bool_res = verify_initial_state(initial_state, root.value)
    result = {'res': 'Result: ' + str(root.value), 'initial_state': 'Initial state '+ str(initial_state) + ": " + str(bool_res)}
    return result

# def process_modelCheckingCTL(filename, formula):
#     cgs = CGS()
#     cgs.read_file(filename)
#     result = model_checking(formula, filename)
#     print(result)
#     return result





