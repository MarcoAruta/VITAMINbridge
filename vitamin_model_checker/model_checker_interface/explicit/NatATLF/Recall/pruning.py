from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.regexParser import is_regex_or_boolean_formula
from vitamin_model_checker.models.CGS import *
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.tree import depth_first_search, reset_pruned_flag, rename_nodes, get_states_from_tree, tree_to_initial_CGS, are_all_nodes_pruned
from vitamin_model_checker.model_checker_interface.explicit.CTL import CTL
from vitamin_model_checker.model_checker_interface.explicit.CTLF import CTLF


pruned_model_file = './tmp.txt'

#Pruning for Regex
def pruning(cgs, tree, height, model, CTLformula, *s_A):
    flag = 0
    #s_A = [{'condition_action_pairs': [('a', 'A'), ('a','B')]}, {'condition_action_pairs': [('a', 'C'), ('a', 'D')]}] #Example strategy to test singular cases
    #print(f"s_A {s_A}"
    for strategy_index, strategy in enumerate(s_A, start=1):
        for iteration, (condition, action) in enumerate(strategy['condition_action_pairs']):
            #individual strategy legit check: to approve the collective strategy, for each individual strategy's guarded action, I check if it's valid
            if legit_strategy_check(cgs, tree, condition, action, strategy_index, model) and cgs.validate_strategy(s_A): #if for each condition's held state, exists at least an outer edge action matching agent's selected action AND the actions' costs sum doesn't exceed resource bound then prune
                print ("LEGIT CHECK STRATEGIA OK")
                if is_regex_or_boolean_formula(condition) == "Boolean Formula":
                    print(f"action {action}")
                    flag = boolean_pruning(cgs, tree, condition, action, strategy_index, model)  # Estende il pruning per tutte le condizioni booleane
                    print(f"Pruned tree for agent {strategy_index}:")
                    print(tree)
                    if are_all_nodes_pruned(tree):
                        print("All nodes are pruned")
                    else:
                        print("Some nodes needs still to be pruned")
                        flag = 0 #There're still other nodes to be pruned, so I force the idle operation
                elif is_regex_or_boolean_formula(condition) == "Regex":
                    print(f"action {action}")
                    print(f"{condition} is a regex")
                    flag = regex_pruning(tree, condition, action, strategy_index, height)
                    print(f"Pruned tree for agent {strategy_index}:")
                    print(tree)
                    if are_all_nodes_pruned(tree):
                        print("All nodes are pruned")
                    else:
                        print("Some nodes needs still to be pruned")
                        flag = 0 #There're still other nodes to be pruned, so I force the idle operation
            else: #strategy not valid, jump to the next collective strategy
                print (f"LEGIT CHECK STRATEGIA NON PASSATO PER {action} data la condition {condition} e agente {strategy_index}")
                return False
            iteration+=1
        if flag == 0:
            #print(f"No action available for agent {strategy_index}, selecting (T, idle)...")
            print(f"Selecting (T, idle) for agent {strategy_index}"),
            flag = idle_pruning(cgs, tree, set(cgs.get_states()), "I", strategy_index, model)  # Estende il pruning per tutte le condizioni booleane
            print(f"Pruned tree for agent {strategy_index} after idle operation:")
            print(tree)
        reset_pruned_flag(tree) #for each indivdual strategy termination inside a whole collective strategy, reboot the node flags

    rename_nodes(tree)
    tree_states = get_states_from_tree(tree)
    print(f"Trasformed Tree {tree}")
    unwinded_CGS = tree_to_initial_CGS(tree, tree_states, cgs.get_number_of_agents(), height)
    print(f"Unwinded CGS {unwinded_CGS}")
    cgs.update_cgs_file(model, pruned_model_file, tree, tree_states, unwinded_CGS)
    result,fks = CTLF.model_checking(cgs, CTLformula, pruned_model_file)
    #result_state_set = eval(result['res'].split(': ')[1])
    #return analyze_solution_states(result_state_set, tree)
    if result[fks.initial] == 1:
        return True, fks, result
    else:
        return False, fks, result


def regex_pruning(tree, condition, action, strategy_index, height):
    path = depth_first_search(tree, condition, height, height)
    if path is None:
        print("No path matches the regex condition")
        return False

    print("Path matching the regex condition:", path)

    def prune_nodes_along_path(node, path, action, strategy_index, current_level):
        entered_statement = 0

        if current_level < len(path) and node.state == path[current_level]:
            to_remove = []
            for i, (child, actions) in enumerate(zip(node.children, node.actions)):
                if (actions[strategy_index - 1] != action) and (not node.pruned):
                    to_remove.append(i)
                    entered_statement = 1 # Set the flag to True when the condition is met
            if entered_statement == 1:
                node.pruned = True  # Set the pruned flag for pruned children
            for i in reversed(to_remove):
                del node.children[i]
                del node.actions[i]

            for child in node.children:
                if prune_nodes_along_path(child, path, action, strategy_index, current_level + 1):
                    entered_statement = 1 # Propagate the True value up if any child returns True

        return entered_statement
    # Call the function and return its result
    return prune_nodes_along_path(tree, path, action, strategy_index, 0)

def boolean_pruning(cgs, tree, condition, action, strategy_index, model):
    cgs.read_file(model)
    states = CTL.model_checking(cgs, str(condition), model)
    state_set = eval(states['res'].split(': ')[1])
    print(f"states where {condition} held {state_set}, dim of states: {len(state_set)}")

    def prune_all_nodes(node, state_set, action, strategy_index, current_level):
        entered_statement = 0

        if node.state in state_set:
            to_remove = []
            for i, (child, actions) in enumerate(zip(node.children, node.actions)):
                if (actions[strategy_index - 1] != action) and (not node.pruned):
                    to_remove.append(i)
                    entered_statement = 1 # Set the flag to True when the condition is met
            if entered_statement == 1:
                node.pruned = True  # Set the pruned flag for pruned children
            for i in reversed(to_remove):
                del node.children[i]
                del node.actions[i]

        for child in node.children:
            if prune_all_nodes(child, state_set, action, strategy_index, current_level + 1):
                entered_statement = 1 # Propagate the True value up if any child returns True

        return entered_statement

    # Call the function and return its result
    return prune_all_nodes(tree, state_set, action, strategy_index, 0)


def legit_strategy_check(cgs, tree, condition, action, strategy_index, model):
    # Verifica se la condition è una regex o una formula booleana
    condition_type = is_regex_or_boolean_formula(condition)

    if condition_type == "Boolean Formula":
        # Se è una formula booleana, esegui il model checking
        cgs.read_file(model)
        states = CTL.model_checking(cgs, condition, model)
        state_set = eval(states['res'].split(': ')[1])
        print(f"states where {condition} held {state_set}, dim of states: {len(state_set)}")
    elif condition_type == "Regex":
        # Se è una regex, trova gli stati usando la funzione regex_pruning
        state_set = set()
        path = depth_first_search(tree, condition, len(tree.children), len(tree.children))
        if path:
            state_set.update(path)
        print(f"states where regex {condition} matched: {state_set}")
    else:
        # Se il tipo non è riconosciuto, solleva un'eccezione
        raise ValueError(f"Unrecognized condition type: {condition_type}")

    # Caso speciale: se state_set è vuoto, ritorna True automaticamente
    if not state_set:
        return True

    def check_all_nodes(node, state_set, action, strategy_index):
        if node.state in state_set:
            action_exists = False
            for i, (child, actions) in enumerate(zip(node.children, node.actions)):
                if actions[strategy_index - 1] == action:
                    action_exists = True
                    break  # Se almeno un'azione valida è trovata, esci dal ciclo
            if not action_exists:
                return False

        for child in node.children:
            if check_all_nodes(child, state_set, action, strategy_index):
                return True

        return True

    return check_all_nodes(tree, state_set, action, strategy_index)


def idle_pruning(cgs, tree, state_set, action, strategy_index, model):
    cgs.read_file(model)

    def prune_all_nodes(node, state_set, action, strategy_index, current_level):
        entered_statement = 0

        if node.state in state_set:
            to_remove = []
            for i, (child, actions) in enumerate(zip(node.children, node.actions)):
                if (actions[strategy_index - 1] != action) and (not node.pruned):
                    to_remove.append(i)
                    #node.pruned = True # Set the pruned flag for pruned children
                    entered_statement = 1 # Set the flag to True when the condition is met
            if entered_statement == 1:
                node.pruned = True  # Set the pruned flag for pruned children
            for i in reversed(to_remove):
                del node.children[i]
                del node.actions[i]

        for child in node.children:
            if prune_all_nodes(child, state_set, action, strategy_index, current_level + 1):
                entered_statement = 1 # Propagate the True value up if any child returns True

        return entered_statement

    # Call the function and return its result
    return prune_all_nodes(tree, state_set, action, strategy_index, 0)