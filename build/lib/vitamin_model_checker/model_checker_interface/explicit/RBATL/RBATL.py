import sys
from vitamin_model_checker.models.costCGS.costCGS import *
from binarytree import Node
from vitamin_model_checker.logics.RBATL import *


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
        states_proposition = get_states_prop_holds(str(tpl))
        if states_proposition is None:
            return None
        else:
            for element in states_proposition:
                states.add(cCGS.get_state_name_by_index(element))
            root = Node(str(states))
    return root

# # Compute the cost of the joint action (RBATL)
# def Cost(actions, state, coalition):
#     total = sys.maxsize
#     for action in actions:
#         max_action = 0
#         for action1 in actions:
#             for i in coalition:
#                 if action[int(i)-1] != action1[int(i)-1]:
#                     break
#             else:
#                 max_action = max(get_cost_for_action(action1, 's'+str(state)), max_action)
#         total = min(max_action, total)
#     return total

# Compute the cost of the joint action (RBATL)
def goodActionsCost(actions, state, bound):
    good_actions = set()
    for action in actions:
        if cCGS.get_cost_for_action(action, 's'+str(state)) <= bound:
            good_actions.add(action)
    return good_actions
        
# It returns the states from which the coalition has a strategy to enforce the next state to lie in state_set.
# function used by the model checker.
def pre(coalition, state_set, bound):
    agents = cCGS.get_agents_from_coalition(coalition)
    graph = cCGS.get_graph()
    state_set = convert_state_set(state_set)  # returns a set of indexes
    pre_states = set()
    dict_state_action = dict()  # dictionary state-action
    for i, source in enumerate(graph):  # take states that have at least one transition to one of the states in the set
        for j in state_set:
            if graph[i][j] != 0:
                coordinates = str(i) + "," + str(j)
                actions_list = cCGS.build_list(graph[i][j])
                goodActions = goodActionsCost(actions_list, i, bound)
                if goodActions:
                    dict_state_action.update({coordinates: goodActions})

    # iterate over these states and check that my move is not present in any other state
    for key, value in dict_state_action.items():
        other_actions_in_row = dict()  # dictionary containing other moves of the row (excluding those saved in dict_state_action).
        all_actions_in_row = set()  # all elements in the row
        i = int(key.split(',')[0])
        j = int(key.split(',')[1])
        for index, element in enumerate(graph[i]):
            if element != 0:
                coordinates = str(i) + "," + str(index)
                all_actions_in_row.update(cCGS.build_list(graph[i][index]))
                if index != j:
                    other_actions_in_row.update({coordinates: cCGS.build_list(graph[i][index])})

        # check if there is a loop -> if yes, it is a pre
        for y in value:
            if '*' in y:
                pre_states.add(str(i))
                break

        for action in value:
            move = cCGS.get_coalition_action(set([action]), agents)
            # checks whether a move is present in the others
            check_passed = True
            for k, v in other_actions_in_row.items():
                other_act = cCGS.get_coalition_action(v, agents)
                if move.intersection(other_act): # they have something in common
                    # check if it belongs to the set
                    column = int(k.split(',')[1])
                    if column not in state_set:
                        check_passed = False
            if check_passed == True:
                pre_states.add(i)

    # take the elements of the set and check if the moves towards the state contain all the possible opponent moves
    result = set()
    for i in pre_states:
        i = int(i)
        opponent_moves_in_state = set()
        opponent_moves_in_row = set()
        for j, column in enumerate(graph[int(i)]):
            if graph[i][j] != 0:
                opponent_moves_in_row.update(cCGS.get_opponent_moves(cCGS.build_list(graph[i][j]), agents))

                if j in state_set:
                    # takes the opponent's moves for actions towards the states in state_set
                    opponent_moves_in_state.update(cCGS.get_opponent_moves(cCGS.build_list(graph[i][j]), agents))

        if opponent_moves_in_row == opponent_moves_in_state:
            # convert i into corresponding state
            result.add(cCGS.get_state_name_by_index(i))
    return result

def extract_coalition_and_cost(string):
    tmp = string[1:].split(">")
    coalition = tmp[0]
    cost = [int(i) for i in tmp[1][1:].split(',')]
    return (coalition, cost)

def inc_bound(bound_p, bound):
    for i in range(0, len(bound_p)):
        if bound[i] == 0:
            bound_p[i] = 0
        else:
            bound_p[i] = (bound_p[i]+1) % (bound[i]+1)
        if bound_p[i] != 0:
            break
def diff_bound(bound1, bound2):
    bound = [0]*len(bound1)
    for i in range(0, len(bound1)):
        bound[i] = bound1[i]-bound2[i]
    return bound

solve_tree_cache = dict()

# function that solves the formula tree. The result is the model checking result.
# It solves every node depending on the operator.
def solve_tree(node):
    key = str(node.value) + (str(node.left) if node.left is not None else '') + (str(node.right) if node.right is not None else '')
    if key in solve_tree_cache:
        node.value = solve_tree_cache[key]
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

        elif verify('COALITION_BOUND', node.value) and verify('GLOBALLY', node.value):  # e.g. <1>Gφ
            coalition_and_bound = extract_coalition_and_cost(node.value)
            coalition = coalition_and_bound[0] # extract the coalition of agents
            bound = coalition_and_bound[1] # extract the bound b assigned to the strategies
            states = string_to_set(node.left.value)
            if not any(bound):
                p = set(cCGS.get_states())
                t = states
                while p - t:  # p not in t
                    p = t
                    t = pre(coalition, p, bound) & states
                node.value = str(p)
            else:
                p = set()
                t = set()
                value_backup = node.value
                bound_p = [0]*len(bound)
                while True:
                    node.value = value_backup[:value_backup[1:].index('<')+1] + '<' + ','.join([str(b) for b in bound_p]) + '>G'
                    solve_tree(node)
                    t = pre(coalition, string_to_set(node.value), diff_bound(bound, bound_p)) & states
                    while p - t:  # p not in t
                        p.update(t)
                        t = pre(coalition, p, [0]*len(bound)) & states
                    inc_bound(bound_p, bound)
                    if bound_p == bound: break
                node.value = str(p)            

        elif verify('COALITION_BOUND', node.value) and verify('NEXT', node.value):  # e.g. <1>Xφ
            # coalition = node.value[1:-2]
            coalition_and_bound = extract_coalition_and_cost(node.value)
            coalition = coalition_and_bound[0] # extract the coalition of agents
            bound = coalition_and_bound[1] # extract the bound b assigned to the strategies
            states = string_to_set(node.left.value)
            ris = pre(coalition, states, bound)
            node.value = str(ris)

        elif verify('COALITION_BOUND', node.value) and verify('EVENTUALLY', node.value):  # e.g. <1>Fφ
            # trueUϕ.
            # coalition = node.value[1:-2]
            coalition_and_bound = extract_coalition_and_cost(node.value)
            coalition = coalition_and_bound[0] # extract the coalition of agents
            bound = coalition_and_bound[1] # extract the bound b assigned to the strategies
            states1 = set(cCGS.get_states())
            states2 = string_to_set(node.left.value)
            if not any(bound):
                p = set()
                t = states2
                while t - p:  # t not in p
                    p.update(t)
                    t = pre(coalition, p, bound) & states1
                node.value = str(p)
            else:
                p = set()
                t = set()
                value_backup = node.value
                bound_p = [0]*len(bound)
                while True:
                    node.value = value_backup[:value_backup[1:].index('<')+1] + '<' + ','.join([str(b) for b in bound_p]) + '>F'
                    solve_tree(node)
                    t = pre(coalition, string_to_set(node.value), diff_bound(bound, bound_p)) & states1
                    while t - p:  # t not in p
                        p.update(t)
                        t = pre(coalition, p, [0]*len(bound)) & states1
                    inc_bound(bound_p, bound)
                    if bound_p == bound: break
                node.value = str(p)

    if node.left is not None and node.right is not None:  # BINARY OPERATORS: or, and, until, implies
        if verify('OR', node.value): # e.g. φ || θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.union(states2)
            node.value = str(ris)

        elif verify('COALITION_BOUND', node.value) and verify('UNTIL', node.value):  # e.g. <1>φUθ
            # coalition = node.value[1:-2]
            coalition_and_bound = extract_coalition_and_cost(node.value)
            coalition = coalition_and_bound[0] # extract the coalition of agents
            bound = coalition_and_bound[1] # extract the bound b assigned to the strategies
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            if not any(bound):
                p = set()
                t = states2
                while t - p:  # t not in p
                    p.update(t)
                    t = pre(coalition, p, bound) & states1
                node.value = str(p)
            else:
                p = set()
                t = set()
                value_backup = node.value
                bound_p = [0]*len(bound)
                while True:
                    node.value = value_backup[:value_backup[1:].index('<')+1] + '<' + ','.join([str(b) for b in bound_p]) + '>U'
                    solve_tree(node)
                    t = pre(coalition, string_to_set(node.value), diff_bound(bound, bound_p)) & states1
                    while t - p:  # t not in p
                        p.update(t)
                        t = pre(coalition, p, [0]*len(bound)) & states1
                    inc_bound(bound_p, bound)
                    if bound_p == bound: break
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

    if key not in solve_tree_cache:
        solve_tree_cache[key] = node.value

# returns whether the result of model checking is true or false in the initial state
def verify_initial_state(initial_state, string):
    if initial_state in string:
        return True
    return False


# does the parsing of the model, the formula, builds a tree and then it returns the result of model checking
# function called by front_end_CS
def model_checking(formula, filename):
    global cCGS

    if not formula.strip():
        result = {'res': 'Error: formula not entered', 'initial_state': ''}
        return result

    # model parsing
    cCGS = costCGS()
    cCGS.read_file(filename)

    # formula parsing
    res_parsing = do_parsing(formula, cCGS.get_number_of_agents())
    if res_parsing is None:
        result = {'res': "Syntax Error", 'initial_state': ''}
        return result
    root = build_tree(res_parsing)
    if root is None:
        result = {'res': "Syntax Error: the atom does not exist", 'initial_state': ''}
        return result

    # model checking
    solve_tree(root)

    # solution
    initial_state = cCGS.get_initial_state()
    bool_res = verify_initial_state(initial_state, root.value)
    result = {'res': 'Result: ' + str(root.value), 'initial_state': 'Initial state '+ str(initial_state) + ": " + str(bool_res)}
    return result


