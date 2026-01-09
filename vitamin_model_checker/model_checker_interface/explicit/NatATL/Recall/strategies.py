import itertools
from itertools import product
import random
from vitamin_model_checker.models.CGS import *
cgs=CGS()
import os
from vitamin_model_checker.model_checker_interface.explicit.NatATL.NatATLtoCTL import get_agents_from_natatl, natatl_to_ctl, get_k_value
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.matrixParser import matrixParser, matrixParserforTree
found_solution = False

# Funzione per generare le condizioni
def generate_conditions(P, C, max_k):
    conditions = set()

    def generate_condition(k, condition):
        if k == 0:
            condition_str = ' && '.join(condition)
            conditions.add(condition_str)
        else:
            for p in P:
                if p not in condition:
                    new_condition = condition + [p]
                    if len(new_condition) == 1:
                        generate_condition(k - 1, new_condition)
                    elif len(new_condition) > 1:
                        new_condition.sort()
                        new_condition_str = new_condition[0] + " " + random.choice(C) + " "
                        for i in range(1, len(new_condition) - 1):
                            new_condition_str += new_condition[i] + " " + random.choice(C) + " "
                        new_condition_str += new_condition[-1]
                        complexity = len(new_condition_str.split())
                        if complexity <= max_k:
                            generate_condition(k - 1, [new_condition_str])

    for k in range(1, max_k + 1):
        generate_condition(k, [])

    return list(conditions)

# Returns all the conditions (plus the negated ones only if max_k is big enough to do it)
# Funzione per generare le condizioni negate
def generate_negated(input_list, max_k):
    negated_conditions = set()
    for input_str in input_list:
        atomic_props = input_str.split(' && ')
        for combo in itertools.product(['', '!'], repeat=len(atomic_props)):
            negated_props = [f'{combo[i]}{atomic_props[i]}' for i in range(len(atomic_props))]
            new_str = ' && '.join(negated_props)
            complexity = len(new_str.split())
            if "!" in new_str:
                complexity += 1
            if "*" in new_str:
                complexity += 1
            if complexity <= max_k:
                negated_conditions.add(new_str)
    return list(negated_conditions)


def generate_strategies(cartesian_products, k, agents, found_solution):
    print("Generating Strategies...")
    strategies = [list() for _ in range(len(agents))]  # Le strategie sono liste

    # Funzione per cercare una soluzione e generare tutte le combinazioni
    def search_solution(strategies, current_strategy, depth):
        if depth == len(agents):
            yield list(current_strategy)  # Restituisce una copia della lista
        else:
            for agent_strategy in strategies[depth]:
                current_strategy.append(agent_strategy)
                yield from search_solution(strategies, current_strategy, depth + 1)
                current_strategy.pop()

    if not found_solution:
        for index, agent_key in enumerate(cartesian_products):
            cartesian_product = cartesian_products[agent_key]

            for r in range(1, k + 1):
                combinations = itertools.combinations(cartesian_product, r)
                filtered_combinations = [combination for combination in combinations
                                         if len(set(action for _, action in combination)) == r]
                for combination in filtered_combinations:
                    total_complexity = sum(
                        len(str(condition).split()) + (1 if "!" in str(condition) or "*" in str(condition) else 0)
                        for condition, _ in combination)
                    if total_complexity == k:
                        new_strategy = {"condition_action_pairs": list(combination)}
                        if not is_duplicate(strategies[index], new_strategy):
                            strategies[index].append(new_strategy)

        # Ora usiamo un iteratore per generare una strategia collettiva alla volta
        return search_solution(strategies, [], 0)
def is_duplicate(existing_strategies, new_strategy):
    for existing_strategy in existing_strategies:
        if 'condition_action_pairs' in existing_strategy and existing_strategy['condition_action_pairs'] == new_strategy['condition_action_pairs']:
            return True
    return False

class BreakLoop(Exception):
    pass

def agent_combinations(new_combinations):
    for agent1 in new_combinations:
        for agent2 in new_combinations:
            yield agent1, agent2

def initialize(model_path, formula):
    filename = os.path.abspath(model_path)
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"No such file or directory: {filename}")
    cgs.read_file(filename)

    # Testing part: randomize formula
    # randomized_formula = randomize_natatl_formula(formula, get_number_of_agents(), get_atomic_prop())
    # with open(f'C:\\Users\\lmfao\\Desktop\\Tesi\\TESTING\\Exists Globally with n agents\\testing5\\modified_formula.txt','w') as f:
    #    f.write(str(randomized_formula))
    # print(randomized_formula)

    graph = cgs.get_graph()
    # Check if input model is correct
    matrixParser(graph, cgs.get_number_of_agents())
    matrixParserforTree(graph, cgs.get_number_of_agents())
    # Transform natATL formula into CTL formula
    CTLformula = natatl_to_ctl(formula)
    print(formula)
    print(CTLformula)
    k = get_k_value(formula)
    s = cgs.get_states()
    print(f"STATES: {s}")
    print(cgs.get_matrix_proposition())
    # Modify to return a list of agents if I have complex formulas
    agents = get_agents_from_natatl(formula)
    print(f"Envolved agents: {agents}")
    actions_per_agent = cgs.get_actions(agents)
    print(f"actions picked by each agent:{actions_per_agent}")
    agent_actions = {}
    for i, agent_key in enumerate(actions_per_agent.keys()):
        agent_actions[f"actions_{agent_key}"] = actions_per_agent[agent_key]
    # print(f"Obtained actions: {agent_actions}")
    actions_list = [actions for actions in agent_actions.values()]
    atomic_propositions = cgs.get_atomic_prop()
    print(atomic_propositions)
    return k, agent_actions, actions_list, atomic_propositions, CTLformula, agents, filename, cgs


# Funzione per creare le espressioni regolari
def create_reg_exp(k, atomic_propositions):
    C = ['and', 'or']
    print(f"k corrente: {k}")
    #R = ['composition', 'nondetChoice']
    R = ['.']
    conditions = generate_conditions(atomic_propositions, C, k)
    negated_conditions = generate_negated(conditions, k)
    stories = generate_stories(negated_conditions, k)
    all_conditions = set(negated_conditions) | set(stories)  # unifica entrambi gli insiemi
    regular_expressions = generate_regular_expression(all_conditions, R, k)
    return regular_expressions


def generate_guarded_action_pairs(reg_exp_list, agent_actions):
    result = {}
    for i, actions in enumerate(agent_actions):
        agent_key = f'actions_agent{i + 1}'
        cartesian_product = list(product(reg_exp_list, actions))
        result[agent_key] = cartesian_product
    return result

# Funzione per generare le storie
def generate_stories(input_set, max_k):
    stories = set()
    for input_str in input_set:
        atomic_props = input_str.split(' && ')
        for combo in itertools.product(['', '*'], repeat=len(atomic_props)):
            story = [f'{atomic_props[i]}{combo[i]}' if combo[i] != '' else atomic_props[i] for i in range(len(atomic_props))]
            new_str = ' && '.join(story)
            complexity = len(new_str.split())
            if "*" in new_str:
                complexity += 1
            if "!" in new_str:
                complexity += 1
            if complexity <= max_k and "*" in new_str:
                stories.add(new_str)
    return list(stories)

# Funzione per generare le espressioni regolari
def generate_regular_expression(P, R, max_k):
    expressions = set()

    def generate_expression(k, expression):
        if k == 0:
            condition_str = ' && '.join(expression)
            expressions.add(condition_str)
        else:
            for p in P:
                if p not in expression:
                    new_condition = expression + [p]
                    if len(new_condition) == 1:
                        generate_expression(k - 1, new_condition)
                    elif len(new_condition) > 1:
                        new_condition_str = new_condition[0] + " " + random.choice(R) + " "
                        for i in range(1, len(new_condition) - 1):
                            new_condition_str += new_condition[i] + " " + random.choice(R) + " "
                        new_condition_str += new_condition[-1]
                        complexity = len(new_condition_str.split()) + new_condition_str.count('!') + new_condition_str.count('*')
                        if complexity <= max_k:
                            generate_expression(k - 1, [new_condition_str])

    for k in range(1, max_k + 1):
        generate_expression(k, [])

    return list(expressions)
