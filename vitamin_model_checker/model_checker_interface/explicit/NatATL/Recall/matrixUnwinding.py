from vitamin_model_checker.models.CGS import *
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.witnessParser import RegexWitnessGenerator, store_word
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.regexParser import check_prop_holds_in_label_row
import random
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.strategies import cgs


class TreeNode(object):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.level = 0  # Aggiunto il campo level
        self.children = []
        self.actions = []
        self.true_props = []
        self.path_true_props = []
        self.label_row = get_label_row_list(self, cgs.get_states(), cgs.get_matrix_proposition())
        self.predecessors = {}
        self.visited_depths = set()  # Set per memorizzare le profondità già visitate per il nodo
        self.visitedBool = False

    def add_child(self, child_node, actions):
        self.children.append(child_node)
        self.actions.append(actions)


    def update_true_props(self, parent_node):
        for true_prop in parent_node.path_true_props:
            if true_prop not in self.path_true_props:
                self.path_true_props.append(true_prop)

    def __repr__(self, level=0, max_depth=2):
        if level > max_depth:
            return ''
        ret = "\t" * level + repr(self.state) + "\n"
        ret += "\t" * level + "Level: " + str(self.level) + "\n"
        ret += "\t" * level + "Label Row: " + str(self.label_row) + "\n"
        ret += "\t" * level + "True Props: " + str(self.true_props) + "\n"
        ret += "\t" * level + "Path True Props: " + str(self.path_true_props) + "\n"
        ret += "\t" * level + "Predecessors: " + str(self.predecessors) + "\n"
        for child, actions in zip(self.children, self.actions):
            action_str = ', '.join([f'{k}: {v}' for action in actions for k, v in action.items()])
            ret += "\t" * (level + 1) + "Actions: " + action_str + "\n"
            ret += child.__repr__(level + 1, max_depth)
            child.update_true_props(self)
        #current_predecessors.clear()
        return ret


def build_tree_from_edges(edges, root_state='s0', max_depth=2):
    nodes = {root_state: TreeNode(root_state)}
    visited = set()
    states_list = [] #list to store the states and to pass them as list to get_atomic_propositions_for_states(), as required from the function
    def add_edges_to_tree(parent_state, current_depth):
        if current_depth > max_depth or parent_state in visited:
            return
        visited.add(parent_state)
        #current_predecessors = predecessors + [node.state]
        for edge in edges:
            if edge[0] == parent_state:
                _, child_state, actions = edge
                if child_state not in nodes:
                    nodes[child_state] = TreeNode(child_state)
                nodes[parent_state].add_child(nodes[child_state], actions)
                add_edges_to_tree(child_state, current_depth + 1)
                states_list.append(child_state)
                true_props_dict = cgs.get_atomic_propositions_for_states(cgs.get_atomic_prop(), cgs.get_matrix_proposition(), states_list)
                print(f"true props dict {true_props_dict}")
                nodes[child_state].path_true_props = cgs.get_unique_values_from_dict_values(true_props_dict)
                nodes[child_state].true_props = cgs.get_unique_values_from_dict_values(true_props_dict)
                nodes[child_state].update_true_props(nodes[parent_state])
                states_list.clear()

    add_edges_to_tree(root_state, 0)
    return nodes[root_state]


def populate_true_props(node, max_depth):
    states_list = []
    if max_depth == 0:
        return
    for child_node in node.children:
        states_list.append(child_node.state)
        true_props_dict = cgs.get_atomic_propositions_for_states(cgs.get_atomic_prop(), cgs.get_matrix_proposition(), states_list)
        child_node.path_true_props = cgs.get_unique_values_from_dict_values(true_props_dict)
        child_node.true_props = cgs.get_unique_values_from_dict_values(true_props_dict)
        states_list.clear()
        populate_true_props(child_node, max_depth - 1)

##################################################################################################################################################################
#Prunes all the subtrees that disagree with the selected strategy's actions (valid_actions) for the states where strategy's conditions held (named input_nodes)
def prune_tree(node, valid_actions, input_nodes, index, path, current_depth=0, visited=None):
    if visited is None:
        visited = set()

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
                    if (agent_key in valid_actions and act in valid_actions[agent_key]) or act == "I":  # if that agent lays in valid_actions and its action is in valid_actions also I won't prune
                        valid_action_found = True
                    else:  # otherwise if the action is not valid and it is not IDLE I'll prune
                        # If an invalid action is found, mark this action set for removal
                        valid_action_found = False
                        break
                if valid_action_found:
                    updated_actions.append(action)

            # If no valid actions remain, mark the child for removal
            if not updated_actions:
                to_remove.append((i, child))
            else:
                # Update the actions with the filtered valid actions
                node.actions[i] = updated_actions

        # Remove marked children and actions
        for i, child in reversed(to_remove):
            del node.children[i]
            del node.actions[i]

    # Recalculate true_props for the pruned tree
    node.true_props.clear()

    # Recursively apply pruning to children, regardless of current node's state
    for child in node.children:
        prune_tree(child, valid_actions, input_nodes, index, path, current_depth + 1, visited)


#########################################################################################################################################
def rename_states(node, current_name_map, next_state_id=0, depth=0, max_depth=2):
    if depth > max_depth:
        return next_state_id
    if node.state not in current_name_map:
        new_state = f's{next_state_id}'
        current_name_map[node.state] = new_state
        next_state_id += 1
    node.state = current_name_map[node.state]
    for child in node.children:
        next_state_id = rename_states(child, current_name_map, next_state_id, depth + 1, max_depth)
    return next_state_id


def rename_duplicate_nodes(root,counter, max_depth=2):
    #state_counter = 1  # Start from s1 because the root is s0

    def traverse_and_rename(node, counter,used, current_depth):
        #nonlocal state_counter
        if current_depth > max_depth:
            return

        #if node is not root:  # Skip renaming the root
        new_state = f's{counter}'

        if new_state not in used:
            print(f"NUOVO STATO RINOMINATO {node.state} -> {new_state}")
            #state_counter += 1
            node.state = new_state
            used.append(new_state)
        else:
            new_state = f's{counter+5}'
            print(f"NUOVO STATO RINOMINATO {node.state} -> {new_state}")
            # state_counter += 1
            node.state = new_state
            used.append(new_state)


        for child in node.children:
            traverse_and_rename(child, counter+1, used,  current_depth + 1)

    traverse_and_rename(root, 0,[], 0)
    return root

#def format_actions(action_str, num_agents):
 #   return action_str  # Assuming this formats action strings correctly based on the previous context


def tree_to_initial_CGS(root, num_agents, max_depth):
    current_name_map = {}
    rename_states(root, current_name_map)

    # Initialize transition matrix with "0" for non-diagonal elements
    transition_matrix = [['0' for _ in range(len(current_name_map))] for _ in range(len(current_name_map))]
    state_index = {state: idx for idx, state in enumerate(sorted(current_name_map.values()))}

    def traverse(node, depth):
        if depth > max_depth or not node:
            return
        state_idx = state_index[node.state]
        for child, actions in zip(node.children, node.actions):
            child_idx = state_index[child.state]
            action_str = ''.join([f'{k}: {v}' for action in actions for k, v in action.items()])
            action_str = format_actions(action_str, num_agents)
            transition_matrix[state_idx][child_idx] = action_str
            traverse(child, depth + 1)

    traverse(root, 0)
    return transition_matrix


def format_actions(string, num_agents):
    for i in range(1, num_agents + 1):
        string = string.replace(f'agent{i}: ', '')
    # Insert a comma every "num_agent actions" inside a matrix element
    formatted_actions = ','.join(string[i:i+num_agents] for i in range(0, len(string), num_agents))
    return formatted_actions


#Assigns the right label_matrix row to the label's node field
def get_label_row_list(self, states, label_matrix):
    for i in range(0, cgs.get_number_of_states()):
        if self.state == states[i]: #example: if self.state is 's0' and states[i] is 's0' then it returns the first row of the label_matrix
            return label_matrix[i]


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


#def depth_first_search(node, predecessors=[], depth=0, max_depth=2):
 #   if not node or depth > max_depth:
  #          return

    # Aggiungiamo il nodo corrente alla lista dei predecessori
    #current_predecessors = predecessors + [node.state]
    #print("State:", node.state)  # Stampa lo stato del nodo corrente
    #print("Label Row:", node.label_row)
    #print("Predecessors:", current_predecessors)  # Stampa la lista dei predecessori del nodo corrente
    #print("At depth:", depth)  # Stampa la lista dei predecessori del nodo corrente
    #print()  # Linea vuota per la chiarezza

    # Visita ricorsivamente i nodi figli fino alla profondità massima
    #for child in node.children:
        #depth_first_search(child, current_predecessors, depth + 1, max_depth)


# Funzione DFS che verifica le parole generate sull'albero
def depth_first_search(node, pattern, length, max_depth=2):
    generator = RegexWitnessGenerator(pattern, length)
    word = generator.next_word()

    while word is not None:
        print(f"word used: {word}")
        stored_word = store_word(word)
        result = dfs_verify_word(node, stored_word, [], 0, max_depth)
        if result is not None:
            return result  # Termina la generazione di altre parole se un percorso soddisfa il pattern
        word = generator.next_word()
    return None


def dfs_verify_word(node, word, predecessors, depth, max_depth):
    if depth == len(word):
        return predecessors  # Abbiamo verificato tutti i caratteri della parola con successo

    if depth > max_depth:
        return None  # Superata la profondità massima

    current_predecessors = predecessors + [node.state]
    print(f"vedi se int di state funziona... {int(node.state[1:])}")
    if check_prop_holds_in_label_row(word[depth], node.label_row):  # if current state satisfies the current character for the word
        if depth == len(word) - 1:  # Abbiamo raggiunto l'ultimo carattere della parola
            print("State:", node.state)
            print("Predecessors:", current_predecessors)
            print("At depth:", depth)
            print()
            return current_predecessors
        for child in node.children:
            result = dfs_verify_word(child, word, current_predecessors, depth + 1, max_depth)
            if result is not None:
                return result
    return None


def set_predecessors(node, predecessors, depth, max_depth, visited_paths):
    current_predecessors = predecessors + [node.state]
    node.predecessors[depth] = current_predecessors

    if current_predecessors not in visited_paths:
        node.level = depth  # Update the level of the node only if the current path is not visited
        visited_paths.append(current_predecessors)
    visited_paths.clear()
    print(f"IL nodo {node.state} ha profondità {depth}")
    print(f"Predecessors of node {node.state} at depth {depth}: {node.predecessors[depth]}")
    node.visited_depths.add(depth)
    if depth < max_depth:
        for child in node.children:
            if depth + 1 not in child.visited_depths:
                set_predecessors(child, current_predecessors, depth + 1, max_depth, visited_paths)


def dfs_remove_predecessors(node, depth, max_depth):
    if depth > max_depth:
        return

    # Rimuovi tutte le chiavi del dizionario predecessori fino alla profondità corrente
    for d in list(node.predecessors.keys()):
        if d <= depth:
            del node.predecessors[d]

    # Stampa il nodo corrente
    print(f"Nodo {node.state}, Predecessors rimossi a depth {depth}: {node.predecessors}")

    # Ricorsione sui figli del nodo corrente
    for child in node.children:
        dfs_remove_predecessors(child, depth + 1, max_depth)


def rinomina_nodi(albero, depth, max_depth=2):
    def rinomina(nodo, counter, depth, max_depth):

        if depth>max_depth:
            return
        nodo.state = f"s{counter}"
        counter += 1
        for figlio in nodo.children:
            counter = rinomina(figlio, counter+1, depth+1, max_depth)
        return counter

    rinomina(albero, 1, 0, 2)


