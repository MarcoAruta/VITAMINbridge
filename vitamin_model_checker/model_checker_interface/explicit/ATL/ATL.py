from binarytree import Node
from vitamin_model_checker.models.CGS.CGS import *
from vitamin_model_checker.logics.ATL import *


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
                states.add(cgs.get_state_name_by_index(element))
            root = Node(str(states))
    return root


# It returns the states from which the coalition has a strategy to enforce the next state to lie in state_set.
# function used by the model checker.
from itertools import product


def pre(coalition, state_set):
    """
    Ritorna l'insieme (di nomi di stato) da cui la coalizione `coalition`
    ha una strategia per forzare la prossima transizione in state_set.

    - coalition: stringa tipo '1,2' o lista di indici agenti
    - state_set: insieme di nomi di stato, es. {'s1','s3'}
    """
    # 1) Indici degli stati target
    T_idx = convert_state_set(state_set)

    # 2) Agenti in A e agenti avversari
    A = cgs.get_agents_from_coalition(coalition)  # es. [0,2]
    all_agents = list(range(cgs.get_number_of_agents()))
    NotA = [i for i in all_agents if i not in A]

    graph = cgs.get_graph()  # matrice |S|×|S|, entry = bitmask di profili
    result = set()

    # 3) Per ciascuno stato q...
    for q in range(len(graph)):
        # raccogliamo tutti i profili di azione possibili in q:
        # joint_moves = [(profilo, stato_successivo_j), ...]
        joint_moves = []
        for j, mask in enumerate(graph[q]):
            if mask != 0:
                for prof in cgs.build_list(mask):
                    joint_moves.append((prof, j))

        # 4) raggruppiamo per mossa di A:
        #   dict: mA_tuple -> [ (mo_tuple, j), ... ]
        # dove mo = mossa degli avversari
        moves_by_A = {}
        for prof, j in joint_moves:
            mA = tuple(sorted(cgs.get_coalition_action({prof}, A)))
            mo = tuple(sorted(cgs.get_opponent_moves({prof}, A)))
            moves_by_A.setdefault(mA, []).append((mo, j))

        # 5) per ciascuna mossa di A cerchiamo di validarla:
        for mA, trans in moves_by_A.items():
            # insieme di tutte le contromosse possibili
            opp_moves = {mo for mo, _ in trans}

            good = True
            # per ogni contromossa o vogliamo che TUTTE le transizioni finiscano in T_idx
            for o in opp_moves:
                # tutte le destinazioni j raggiungibili con (mA,o)
                destinazioni = [j for mo, j in trans if mo == o]
                # se anche una sola destinazione non è in T_idx, mA fallisce
                if not destinazioni or any(j not in T_idx for j in destinazioni):
                    good = False
                    break

            if good:
                # se troviamo almeno una mA che “vince” contro tutte le o,
                # allora q ∈ Pre_A(T)
                result.add(cgs.get_state_name_by_index(q))
                break

    return result


# function that solves the formula tree. The result is the model checking result.
# It solves every node depending on the operator.
def solve_tree(node):
    if node.left is not None:
        solve_tree(node.left)
    if node.right is not None:
        solve_tree(node.right)

    if node.right is None:   # UNARY OPERATORS: not, globally, next, eventually
        if verify('NOT', node.value):  # e.g. ¬φ
            states = string_to_set(node.left.value)
            all_states = set(cgs.get_states())
            ris = all_states - states
            node.value = str(ris)

        elif verify('COALITION', node.value) and verify('GLOBALLY', node.value):  # e.g. <1>Gφ
            coalition = node.value[1:-2]
            states = string_to_set(node.left.value)
            p = set(cgs.get_states())
            t = states
            while p - t:  # p not in t
                p = t
                t = pre(coalition, p) & states
            node.value = str(p)

        elif verify('COALITION', node.value) and verify('NEXT', node.value):  # e.g. <1>Xφ
            coalition = node.value[1:-2]
            states = string_to_set(node.left.value)
            ris = pre(coalition, states)
            node.value = str(ris)

        elif verify('COALITION', node.value) and verify('EVENTUALLY', node.value):  # e.g. <1>Fφ
            # trueUϕ.
            coalition = node.value[1:-2]
            states = string_to_set(node.left.value)
            p = set()
            t = states
            while t - p:  # t not in p
                p.update(t)
                t = pre(coalition, p)
            node.value = str(p)

    if node.left is not None and node.right is not None:  # BINARY OPERATORS: or, and, until, implies
        if verify('OR', node.value): # e.g. φ || θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.union(states2)
            node.value = str(ris)

        elif verify('COALITION', node.value) and verify('UNTIL', node.value):  # e.g. <1>φUθ
            coalition = node.value[1:-2]
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            p = set()
            t = states2
            while t - p:  # t not in p
                p.update(t)
                t = pre(coalition, p) & states1
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

    # solution
    initial_state = cgs.get_initial_state()
    bool_res = verify_initial_state(initial_state, root.value)
    result = {'res': 'Result: ' + str(root.value), 'initial_state': 'Initial state '+ str(initial_state) + ": " + str(bool_res)}
    return result