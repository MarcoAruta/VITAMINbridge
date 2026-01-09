from vitamin_model_checker.models.CGS import *
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.witnessParser import RegexWitnessGenerator, store_word
from vitamin_model_checker.model_checker_interface.explicit.CTL import build_tree, verify_initial_state
from vitamin_model_checker.models.CGS import *
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.regexParser import do_parsing_boolean, solve_regex_tree, check_prop_holds_in_label_row
class Node:
    def __init__(self, name, cgs, action=None, predecessors=None):
        self.cgs = cgs
        self.state = str(name)
        self.action = action
        self.children = []
        self.predecessors = [str(p) for p in predecessors] if predecessors is not None else []
        self.label_row = self.get_label_row_list(cgs.get_states(), cgs.get_matrix_proposition())
        self.actions = []
        self.old_state = name
        self.pruned = False

    def add_child(self, child, action=None):
        self.children.append(child)
        if action:
            self.actions.append(action)

    def __repr__(self, level=0):
        ret = "\t" * level + repr(self.state)
        if self.action:
            ret += f" ({self.action})"
        ret += "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret

    def __str__(self, level=0):
        ret = " " * level + f"Nome: {self.state}, Vecchio Nome: {self.old_state}, Azione: {self.action}, Predecessori: {self.predecessors}, Label Row: {self.label_row}, Pruned Flag: {self.pruned}\n"
        for child in self.children:
            ret += child.__str__(level + 1)
        return ret

    def get_label_row_list(self, states, label_matrix):
        for i in range(0, self.cgs.get_number_of_states()):
            if self.state == states[i]:
                return label_matrix[i]

def build_tree_from_CGS(CGS, model_states, height):
    def add_children(node, current_level):
        if current_level >= height:
            return

        state_index = int(node.state[1:])
        transitions = CGS.get_graph()[state_index]

        for next_state_index, actions in enumerate(transitions):
            if actions == 0:  # Controllo per saltare le transizioni nulle
                continue

            next_state = str(model_states[next_state_index])
            for action in actions.split(','):
                if next_state not in nodes:
                    nodes[next_state] = Node(next_state, CGS)

                new_child = Node(next_state, CGS, action=action, predecessors=node.predecessors + [node.state])
                node.add_child(new_child, action=action)
                nodes[f"{node.state}_{action}_{next_state}"] = new_child

                add_children(new_child, current_level + 1)

    root = Node("s0", CGS)
    nodes = {"s0": root}

    add_children(root, 1)

    return root


def rename_nodes(tree):
    def rename(node, counter):
        for child in node.children:
            child.state = f"s{counter}"  # Aggiorna solo il campo state
            counter += 1
            counter = rename(child, counter)
        return counter

    rename(tree, 1)

# Funzione di pruning adattata
def prune_tree(node, valid_actions, input_nodes, index, path, height, current_depth=0, visited=None):
    if visited is None:
        visited = set()

    if path:
        if node is None or node.state in visited or current_depth >= len(path):
            return

    visited.add(node.state)

    # Only prune if the current node is in the input_nodes list and matches the current path state
    if node.state in input_nodes and node.state == path[current_depth]:
        to_remove = []
        for i, (child, actions) in enumerate(zip(node.children, node.actions)):
            updated_actions = []
            for action in actions:  # for actions starting from the selected input_nodes
                valid_action_found = False
                # Determine the agent key based on the index
                agent_key = f"agent{index}"
                # Check if the specific agent related to the index is in the action
                if agent_key in action:
                    act = action[agent_key]
                    # Check if the action is valid or marked as "I"
                    if (agent_key in valid_actions and act in valid_actions[agent_key]) or act == "I":
                        valid_action_found = True
                    else:
                        valid_action_found = False
                        break
                if valid_action_found:
                    updated_actions.append(action)

            if not updated_actions:
                to_remove.append((i, child))
            else:
                node.actions[i] = updated_actions

        for i, child in reversed(to_remove):
            del node.children[i]
            del node.actions[i]

    for child in node.children:
        prune_tree(child, valid_actions, input_nodes, index, path, height, current_depth + 1, visited)


def get_states_from_tree(root):
    states = []

    def traverse(node):
        if node.state not in states:
            states.append(node.state)
        for child in node.children:
            traverse(child)

    traverse(root)
    return states


def tree_to_initial_CGS(root, states, num_agents, max_depth):
    state_index = {state: idx for idx, state in enumerate(states)}

    transition_matrix = [['0' for _ in range(len(state_index))] for _ in range(len(state_index))]

    def traverse(node, depth):
        if depth > max_depth or not node:
            return
        state_idx = state_index[node.state]
        for child, actions in zip(node.children, node.actions):
            child_idx = state_index[child.state]
            # Convert action string to numerical value or probability
            action_value = str(actions)
            transition_matrix[state_idx][child_idx] = action_value
            traverse(child, depth + 1)

    traverse(root, 0)
    return transition_matrix



def depth_first_search(node, pattern, length, max_depth=2):
    generator = RegexWitnessGenerator(pattern, length)
    word = generator.next_word()

    while word is not None:
        print(f"word used: {word}")
        stored_word = store_word(word)
        result = dfs_verify_word(node, stored_word, [], 0, max_depth)
        if result is not None:
            return result
        word = generator.next_word()
    return None

def dfs_verify_word(node, word, predecessors, depth, max_depth):
    if depth == len(word):
        return predecessors

    if depth > max_depth:
        return None

    current_predecessors = predecessors + [node.state]
    if check_prop_holds_in_label_row(word[depth], node.label_row):
        if depth == len(word) - 1:
            return current_predecessors
        for child in node.children:
            result = dfs_verify_word(child, word, current_predecessors, depth + 1, max_depth)
            if result is not None:
                return result
    return None


def get_label_row_list(self, states, label_matrix):
    for i in range(0, self.cgs.get_number_of_states()):
        if self.state == states[i]:
            return label_matrix[i]

def get_states_prop_holds(self, formula):
    print(f"formula to parse: {formula}")
    res_parsing = do_parsing_boolean(str(formula))
    if res_parsing is None:
        result = {'res': "Syntax Error", 'initial_state': ''}
        return result
    root = build_tree(res_parsing)
    if root is None:
        result = {'res': "Syntax Error: the atom does not exist", 'initial_state': ''}
        return result
    print(f"root is: {root}")
    solve_regex_tree(root, self.cgs.get_edges())

    initial_state = self.cgs.get_initial_state()
    bool_res = verify_initial_state(initial_state, root.value)
    result = {'res': 'Result: ' + str(root.value), 'initial_state': 'Initial state '+ str(initial_state) + ": " + str(bool_res)}
    return result

def reset_pruned_flag(node):
    node.pruned = False
    for child in node.children:
        reset_pruned_flag(child)

def are_all_nodes_pruned(tree):
    """
    Verifica se tutti i nodi di un albero hanno il campo pruned impostato a True.

    Args:
        tree (Node): Radice dell'albero.

    Returns:
        bool: True se tutti i nodi hanno il campo pruned a True, False altrimenti.
    """
    if tree.pruned == False:
        return False
    for child in tree.children:
        if not are_all_nodes_pruned(child):
            return False
    return True

# funzione per analizzare gli stati soluzione a partire dall'albero per verificare se lo stato iniziale s0 è presente nei predecessori :
#in particolare dal momento che il tree è rinominato, si analizza sia il campo old_state che tiene traccia dei vecchi nodi per analizzare anche il nodo "corrente" che i suoi predecessori
#per appurare che realmente s0 sia presente nella soluzione e che sia realmente una soluzione attendibile
def analyze_solution_states(solution_states, root):
    def traverse(node, result):
        if node.state in solution_states:
            print(f"State: {node.state}, Old State: {node.old_state}, Predecessors: {node.predecessors}")
            result.add(node)
        for child in node.children:
            traverse(child, result)

    result_set = set()
    traverse(root, result_set)

    for node in result_set:
        if 's0' in node.old_state or 's0' in node.predecessors:
            print("Il nodo iniziale è presente nei predecessori dell'albero originale")
            return True
    return False


##################################ESEMPIO D'USO ####################################################################
# Creazione e stampa dell'albero prima della rinominazione
#CGS = [['II', 'AC'], ['BD', 'II']]
#model_states = ["s0", "s1"]
#height = 3  # Altezza desiderata per l'albero

#tree = build_tree_from_CGS(CGS, model_states, height)
#print("Albero prima della rinominazione:")
#print(tree)

# Rinomina dei nodi
#rename_nodes(tree)

# Stampa dell'albero dopo la rinominazione:
#print("Albero dopo la rinominazione:")
#print(tree)

# Stampa dettagliata con predecessori
#print("Dettagli nodi con predecessori:")
#print(tree)




