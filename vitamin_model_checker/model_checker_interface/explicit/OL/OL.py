from vitamin_model_checker.models.costCGS.costCGS import *
from binarytree import Node
from vitamin_model_checker.logics.OL import *
from timeit import default_timer as timer

last_filename = ""
pre_set_array = []

# returns the states where the proposition holds
def get_states_prop_holds(prop):
    states = set()
    prop_matrix = cCGS.get_matrix_proposition()

    index = cCGS.get_atom_index(prop)
    if index is None:
        return None
    for state, source in enumerate(prop_matrix):
        if source[int(index)] == 1:
            states.add(state)
    return states



# set of states (ex. s1, s2) as input and returns a set of indices to identify them
def convert_state_set(state_set):
    states = set()
    for elem in state_set:
        position = cCGS.get_index_by_state_name(elem)
        states.add(int(position))
    return states
    
def convert_indices_state_set(indices_state_set):
    states = set()
    for elem in indices_state_set:
        states.add(cCGS.get_state_name_by_index(elem))
    return states


# converts a string into a set
def string_to_set(string):
    if string == 'set()':
        return set()
    set_list = string.strip("{}").split(", ")
    new_string = "{" + ", ".join(set_list) + "}"
    return eval(new_string)


#  function that builds a formula tree, used by the model checker
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
        if (verify('FALSE', str(tpl))):
            return Node(str(states))
        elif (verify('TRUE', str(tpl))):
            return Node(str(set(cCGS.get_states())))
        states_proposition = get_states_prop_holds(str(tpl))
        if states_proposition is None:
            return None
        else:
            for element in states_proposition:
                states.add(cCGS.get_state_name_by_index(element))
            root = Node(str(states))
    return root

def complement(state_set):
    result = set()
    graph = cCGS.get_graph()
    if (len(graph) - len(state_set) <= 0): 
        return result
    for i in range(0, len(graph)):
        if (i not in state_set):
            result.add(i)
    return result

	
# pre with standard matrix
def pre(state_set):
    result = set()
    graph = cCGS.get_graph()
    for i, source in enumerate(graph):  # take states that have at least one transition to one of the states in the set
        for j in state_set:
            if graph[i][j] != 0:
                    result.add(i)
                    break
    return result

# builds an array where the j-th element is a set with all the predecessors of the j-th state
def build_pre_set_array():
    graph = cCGS.get_graph()
    graph_len = len(graph)
    result = [set()] * graph_len
    for i in range(0, graph_len):
        for j in range(0, graph_len):
            if graph[i][j] != 0:
                result[j].add(i)
    pre_set_array = result
               
# pre that uses the array of predecessors instead of the graph matrix
def pre_set_variant(state_set):
    result = set()
    for i in state_set:
        for j in pre_set_array[i]:
            result.add(i)
    return result

# triangle "right" operator 
def triangle(s, n, state_set):
    cost = 0
    tCost = 0
    graph = cCGS.get_graph()
    isLoopPresent = False
    for r in state_set:
        if (graph[s][r] != "*"):
            cost += int(graph[s][r])
        else:
            isLoopPresent = True
    # return ((cost <= n and (cost != 0 or isLoopPresent)))
    return (cost <= n)
    
# triangle "down" operator
def triangle_down(n, state_set):
    result = set()
    state_set = convert_state_set(state_set)
    state_set_complement = complement(state_set)
    predecessors = pre(state_set)
    for s in predecessors:
        if (triangle(s, n, state_set_complement)):
            result.add(s)
    return convert_indices_state_set(result)
    
    
# triangle "down" operator
def triangle_down_variant(n, state_set):
    result = set()
    state_set = convert_state_set(state_set)
    state_set_complement = complement(state_set)
    predecessors = pre_set_variant(state_set)
    for s in predecessors:
        if (triangle(s, n, state_set_complement)):
            result.add(s)
    return convert_indices_state_set(result)
    
    
# function that solves the formula tree. The result is the model checking result.
# It solves every node depending on the operator.
def solve_tree(node):
    if node.left is not None:
        solve_tree(node.left)
    if node.right is not None:
        solve_tree(node.right)
    i = 0
    if node.right is None:   # UNARY OPERATORS: not, globally, next, eventually
        if verify('NOT', node.value):  # e.g. ¬φ
            states = string_to_set(node.left.value)
            all_states = set(cCGS.get_states())
            ris = all_states - states
            node.value = str(ris)

        elif verify('DEMONIC', node.value) and verify('GLOBALLY', node.value):  # e.g. <Jn>Gφ
            #<Jn>falseRφ
            n = int(node.value[2:-2])
            states1 = set()
            states2 = string_to_set(node.left.value)
            p = set(cCGS.get_states())
            t = states2
            while t != p: 
                p = t
                t = states2 & (states1 | triangle_down(n, p))
            node.value = str(p)

        elif verify('DEMONIC', node.value) and verify('NEXT', node.value):  # e.g. <Jn>Xφ
            n = int(node.value[2:-2])
            states = string_to_set(node.left.value)
            ris = triangle_down(n, states)
            node.value = str(ris)

        elif verify('DEMONIC', node.value) and verify('EVENTUALLY', node.value):  # e.g. <Jn>Fφ
            #<Jn>trueUϕ.
            n = int(node.value[2:-2])
            states1 = set(cCGS.get_states())
            states2 = string_to_set(node.left.value)
            p = set()
            t = states2
            while t != p:
                p = t
                t = states2 | (states1 & triangle_down(n, p))
            node.value = str(p)

    if node.left is not None and node.right is not None:  # BINARY OPERATORS: or, and, until, implies
        if verify('OR', node.value): # e.g. φ || θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.union(states2)
            node.value = str(ris)

        elif verify('DEMONIC', node.value) and verify('UNTIL', node.value):  # e.g. <Jn>φUθ
            n = int(node.value[2:-2])
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            p = set()
            t = states2
            while t != p: 
                p = t
                t = states2 | (states1 & triangle_down(n, p))
            node.value = str(p)
        elif verify('DEMONIC', node.value) and verify('RELEASE', node.value): #e.g. <Jn>φRθ
            n = int(node.value[2:-2])
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            p = set(cCGS.get_states())
            t = states2
            while t != p: 
                p = t
                t = states2 & (states1 | triangle_down(n, p))
            node.value = str(p)
        elif verify('DEMONIC', node.value) and verify('WEAK', node.value): #e.g. <Jn>φWθ
            #<Jn>(θ R (φ ∨ θ))
            n = int(node.value[2:-2])
            states1 = string_to_set(node.right.value)
            states2 = string_to_set(node.left.value) | states1
            p = set(cCGS.get_states())
            t = states2
            while t != p: 
                p = t
                t = states2 & (states1 | triangle_down(n, p))
            node.value = str(p)
        
        elif verify('AND', node.value):  # e.g. φ && θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.intersection(states2)
            node.value = str(ris)

        elif verify('IMPLIES', node.value):  # e.g. φ -> θ
            # p -> q ≡ ¬p ∨ q
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            not_states1 = set(cCGS.et_states()).difference(states1)
            ris = not_states1.union(states2)
            node.value = str(ris)
            
def solve_tree_adjacency_list(node):
    if node.left is not None:
        solve_tree(node.left)
    if node.right is not None:
        solve_tree(node.right)
    if node.right is None:   # UNARY OPERATORS: not, globally, next, eventually
        if verify('NOT', node.value):  # e.g. ¬φ
            states = string_to_set(node.left.value)
            all_states = set(cCGS.get_states())
            ris = all_states - states
            node.value = str(ris)

        elif verify('DEMONIC', node.value) and verify('GLOBALLY', node.value):  # e.g. <Jn>Gφ
            #<Jn>falseRφ
            n = int(node.value[2:-2])
            states1 = set()
            states2 = string_to_set(node.left.value)
            p = set(cCGS.get_states())
            t = states2
            while t != p: 
                p = t
                t = states2 & (states1 | triangle_down_variant(n, p))
                i+=1
            node.value = str(p)

        elif verify('DEMONIC', node.value) and verify('NEXT', node.value):  # e.g. <Jn>Xφ
            n = int(node.value[2:-2])
            states = string_to_set(node.left.value)
            ris = triangle_down_variant(n, states)
            node.value = str(ris)

        elif verify('DEMONIC', node.value) and verify('EVENTUALLY', node.value):  # e.g. <Jn>Fφ
            #<Jn>trueUϕ.
            n = int(node.value[2:-2])
            states1 = set(cCGS.get_states())
            states2 = string_to_set(node.left.value)
            p = set()
            t = states2
            while t != p:
                p = t
                t = states2 | (states1 & triangle_down_variant(n, p))
            node.value = str(p)

    if node.left is not None and node.right is not None:  # BINARY OPERATORS: or, and, until, implies
        if verify('OR', node.value): # e.g. φ || θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.union(states2)
            node.value = str(ris)

        elif verify('DEMONIC', node.value) and verify('UNTIL', node.value):  # e.g. <Jn>φUθ
            n = int(node.value[2:-2])
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            p = set()
            t = states2
            while t != p: 
                p = t
                t = states2 | (states1 & triangle_down_variant(n, p))
            node.value = str(p)
        elif verify('DEMONIC', node.value) and verify('RELEASE', node.value): #e.g. <Jn>φRθ
            n = int(node.value[2:-2])
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            p = set(cCGS.get_states())
            t = states2
            while t != p: 
                p = t
                t = states2 & (states1 | triangle_down_variant(n, p))
            node.value = str(p)
        elif verify('DEMONIC', node.value) and verify('WEAK', node.value): #e.g. <Jn>φWθ
            #<Jn>(θ R (φ ∨ θ))
            n = int(node.value[2:-2])
            states1 = string_to_set(node.right.value)
            states2 = string_to_set(node.left.value) | states1
            p = set(cCGS.get_states())
            t = states2
            while t != p: 
                p = t
                t = states2 & (states1 | triangle_down_variant(n, p))
            node.value = str(p)
        
        elif verify('AND', node.value):  # e.g. φ && θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.intersection(states2)
            node.value = str(ris)

        elif verify('IMPLIES', node.value):  # e.g. φ -> θ
            # p -> q ≡ ¬p ∨ q
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            not_states1 = set(cCGS.get_states()).difference(states1)
            ris = not_states1.union(states2)
            node.value = str(ris)



# does the parsing of the model, the formula, builds a tree and then it returns the result of model checking
# function called by front_end_CS
def model_checking(formula, filename):
    global cCGS

    # model parsing
    cCGS = costCGS()
    cCGS.read_file(filename)

    build_pre_set_array()
    if not formula.strip():
        result = {'res': 'Error: formula not entered'}
        return result


    # formula parsing
    res_parsing = do_parsing(formula)
    if res_parsing is None:
        result = {'res': "Syntax Error"}
        return result
    root = build_tree(res_parsing)
    if root is None:
        result = {'res': "Syntax Error: the atom does not exist"}
        return result

    # model checking
    solve_tree(root)

    # solution
    result = {'res': 'Result: ' + str(root.value)}
    return result
    

def model_checking_test(formula, filename): 
    global last_filename, cCGS
    if not formula.strip():
        result = {'res': 'Error: formula not entered'}
        return result

    cCGS = costCGS()
    if (filename != last_filename):
        # model parsing
        cCGS.read_file(filename)
        build_pre_set_array()
        last_filename = filename
        
    # formula parsing
    res_parsing = do_parsing(formula)
    if res_parsing is None:
        result = {'res': "Syntax Error"}
        return result
    root = build_tree(res_parsing)
    if root is None:
        result = {'res': "Syntax Error: the atom does not exist"}
        return result
        
    # model checking
    time1 = timer()
    solve_tree_adjacency_list(root)
    model_checking_time_adjacency_list = timer() - time1
    result_adjacency = root.value
    root = build_tree(res_parsing)
    # model checking
    time1 = timer()
    solve_tree(root)
    model_checking_time = timer() - time1
    if (root.value != result_adjacency):
        not_equal.append(formula)
    if (root.value != "set()"):
        res_str = root.value
    else:
        res_str = "None"
    result = {'res': res_str, 'time': model_checking_time, 'time_adjacency_list': model_checking_time_adjacency_list}
    return result