from anytree import Node, RenderTree
from vitamin_model_checker.models.CGS import *

# returns a tree, given the action and the tree set.
def get_coalition_tree(action_coalition, trees):
    for t in trees:
        if t.name == action_coalition:
            return t
    return None


def print_tree(tree):
    for pre, fill, node in RenderTree(tree):
        print(f"{pre}{node.name}")


def build_node(strategy, state, parent):
    node = [state, str(strategy)]
    return node

# returns the atom value in a given state
def get_atom_value(atom_values, state):
    for elem in atom_values:
        if elem[0] == state:
            return elem[1]


# returns a set of trees, one for each action. They represent the next possible move.
def create_next_move_trees(cgs, agents, state):
    destination = 0
    graph = cgs.get_graph()

    # transitions from a state
    index_state = cgs.get_index_by_state_name(state)
    trees = []
    for action in graph[index_state]:
        if action != 0:
            action = cgs.build_list(action)
            for move in action:
                coalition_move = cgs.get_coalition_action(set([move]), agents)

                # create a tree for each action
                t = get_coalition_tree(coalition_move, trees)
                opponent_move = cgs.get_opponent_moves(action, agents)

                if t is None:
                    tree = Node(coalition_move)
                    node = build_node(opponent_move, destination, coalition_move)
                    Node(node, parent=tree)
                    trees.append(tree)

                else:
                    node = build_node(opponent_move, destination, t.name)
                    Node(node, parent=t)

            # ---- end for move ----
        destination = destination + 1
    # ---- end for action ----
    return trees


# evaluates max(min(t1, t2, t3...))
def evaluate_max_strategy(cgs, agents, state, atom_values):

    # builds the strategy tree and then calculates the minimum value
    min_values_tree = []
    trees = create_next_move_trees(cgs, agents, state)

    for el in trees:
        children = el.children
        values_tree = []
        for node in children:
            state = cgs.get_state_name_by_index(node.name[0])
            values_tree.append(get_atom_value(atom_values, state))

        minimum = min(values_tree)
        min_values_tree.append(minimum)

    return max(min_values_tree)

# It returns the states from which the coalition has a strategy to enforce the next state to lie in state_set.
# function used by the model checker.
def pre(cgs, coalition, atom_values):
    # pre for each state
    agents = cgs.get_agents_from_coalition(coalition)
    states = cgs.get_states()
    result = []
    for state in states:
        # coalition strategy from state
        max_value = evaluate_max_strategy(cgs, agents, state, atom_values)
        # put value in the state tuple
        tuple = (state, max_value)
        result.append(tuple)

    # ------ end for state ---------
    result = str(result)
    return result
