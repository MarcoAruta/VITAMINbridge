from vitamin_model_checker.model_checker_interface.explicit.ATLF.pre_ATLF import *
from binarytree import Node
from vitamin_model_checker.logics.ATL import *
from vitamin_model_checker.models.CGS import *


# returns a list of tuples (state, value) where the value depends on the input proposition
def get_tuple_list_prop(prop):
    i = cgs.get_atom_index(prop)
    if i is None:
        return None
    states = cgs.get_states()
    list = []
    matrix = cgs.get_matrix_proposition()

    for index, source in enumerate(matrix):
        tuple = (states[index], float(source[i]))
        list.append(tuple)
    return list


# function that builds a formula tree, used by the model checker
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
        couples = get_tuple_list_prop(tpl)
        if couples is None:
            return None
        root = Node(str(couples))

    return root


# converts a string in a list of tuple (state, value)
def string_to_tuple_list(string):
    list = string.strip("[]").split(", ")
    new_list = []
    for i in range(0, len(list), 2):
        state = list[i].strip("('")
        value = float(list[i + 1].strip(")"))
        new_tuple = (state, value)
        new_list.append(new_tuple)
    return new_list


## returns the minimum between matching values
# e.g. min(states1[2], states2[2])
def intersection_values(states1, states2):
    list = []
    for i in range(0, len(states1)):
        value = min(states1[i][1], states2[i][1])
        tuple = (states1[i][0], value)
        list.append(tuple)
    return list


# assign a value to all tuples (state, value) in the list
def set_value_tuple_list(value):
    list = []
    states = cgs.get_states()
    for i in range(0, len(states)):
        tuple = (states[i], value)
        list.append(tuple)
    return list


# returns if p is in t
def first_included_in_second(p, t):
    # p and t are list of tuples
    for i in range(0, len(p)):
        value_p = p[i][1]
        value_t = t[i][1]
        if value_p > value_t:
            return False
    return True


# returns a new list of tuples with the value of t if value_t is bigger than value_p,
# with the value of p otherwise
def update_values(p, t):
    list = []
    for i in range(0, len(p)):
        value_p = p[i][1]
        value_t = t[i][1]
        if value_t > value_p:
            tuple = (p[i][0], value_t)
        else:
            tuple = (p[i][0], value_p)
        list.append(tuple)
    return list


# returns the difference between matching values
# e.g. states1[2] - states2[2]
def difference_values(states1, states2):
    list = []
    for i in range(0, len(states1)):
        value = states1[i][1] - states2[i][1]
        tuple = (states1[i][0], value)
        list.append(tuple)
    return list


# returns the max between matching values
# e.g. max(states1[2], states2[2])
def union_values(states1, states2):
    list = []
    for i in range(0, len(states1)):
        value = max(states1[i][1], states2[i][1])
        tuple = (states1[i][0], value)
        list.append(tuple)
    return list


# function that solves the formula tree. The result is the model checking result.
# It solves every node depending on the operator.
def solve_tree(node):
    if node.left is not None:
        solve_tree(node.left)
    if node.right is not None:
        solve_tree(node.right)

    if node.right is None:  # UNARY OPERATORS: not, globally, next, eventually
        # ¬φ := 1−φ
        if verify('NOT', node.value):  # e.g. ¬φ
            states = string_to_tuple_list(node.left.value)
            ris = difference_values(set_value_tuple_list(1), states)
            node.value = str(ris)

        if verify('COALITION', node.value) and verify('GLOBALLY', node.value):  # e.g. <1>Gφ
            coalition = node.value[1:-2]
            states = string_to_tuple_list(node.left.value)
            p = set_value_tuple_list(1)  # true
            t = states
            while not first_included_in_second(p, t):  # p not in t
                p = t
                t = intersection_values(eval(pre(cgs,coalition, p)), states)
            node.value = str(p)

        elif verify('COALITION', node.value) and verify('NEXT', node.value):  # e.g. <1>Xφ
            coalition = node.value[1:-2]
            ris = pre(cgs,coalition, eval(node.left.value))
            node.value = str(ris)

        elif verify('COALITION', node.value) and verify('EVENTUALLY', node.value):  # e.g. <1>Fφ
            coalition = node.value[1:-2]
            states = string_to_tuple_list(node.left.value)
            p = set_value_tuple_list(0)
            t = states
            while not first_included_in_second(t, p):  # t not in p
                p = update_values(p, t)
                t = eval(pre(cgs,coalition, p))
            node.value = str(p)

    if node.left is not None and node.right is not None:  # BINARY OPERATORS: or, and, until, implies
        if verify('OR', node.value):  # e.g. φ || θ
            states1 = string_to_tuple_list(node.left.value)
            states2 = string_to_tuple_list(node.right.value)
            res = []
            for i in range(0, len(states1)):
                state = states1[i][0]
                value = max(states1[i][1], states2[i][1])
                tuple = (state, value)
                res.append(tuple)
            node.value = str(res)

        elif verify('AND', node.value):  # e.g. φ && θ
            states1 = string_to_tuple_list(node.left.value)
            states2 = string_to_tuple_list(node.right.value)
            res = []
            for i in range(0, len(states1)):
                state = states1[i][0]
                value = min(states1[i][1], states2[i][1])
                tuple = (state, value)
                res.append(tuple)
            node.value = str(res)

        elif verify('COALITION', node.value) and verify('UNTIL', node.value): # e.g. <1>φUθ
            coalition = node.value[1:-2]
            states1 = string_to_tuple_list(node.left.value)
            states2 = string_to_tuple_list(node.right.value)
            p = set_value_tuple_list(0)
            t = states2
            while not first_included_in_second(t, p):  # t not in p
                p = update_values(p, t)
                t = intersection_values(eval(pre(cgs,coalition, p)), states1)
            node.value = str(p)

        elif verify('IMPLIES', node.value):  # e.g. φ -> θ
            # p -> q ≡ ¬p ∨ q
            states1 = string_to_tuple_list(node.left.value)
            states2 = string_to_tuple_list(node.right.value)
            not_states1 = difference_values(set_value_tuple_list(1), states1)
            ris = union_values(not_states1, states2)
            node.value = str(ris)


# returns the value of the model checking in the initial state
def get_value_initial_state(initial_state, string):
    list_tuple = eval(string)
    for element in list_tuple:
        if element[0] == initial_state:
            return element[1]


# does the parsing of the model, the formula, builds a tree, and then it returns the result of model checking
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
    res_parsing = do_parsing(formula, cgs.get_number_of_agents())
    if res_parsing is None:
        result = {'res': "Syntax Error", 'initial_state': ''}
        return result
    root = build_tree(res_parsing)
    if root is None:
        result = {'res': "Syntax Error: the atom does not exist", 'initial_state': ''}
        return result

    # model checking
    solve_tree(root)

    #solution
    initial_state = cgs.get_initial_state()
    value_initial_state = get_value_initial_state(initial_state, root.value)
    result = {'res': 'Result: ' + str(root.value),
              'initial_state': 'Initial state ' + str(initial_state) + ": " + str(value_initial_state)}
    return result
