import itertools
import random
from vitamin_model_checker.models.CGS import *
import os
from vitamin_model_checker.model_checker_interface.explicit.NatATL.NatATLtoCTL import *

found_solution = False

#this function returns one strategy at time using "yield" keyword
def generate_conditions(P, C, max_k):
    condition_set = set()

    def generate_condition(k, condition):
        if k == 0:
            condition_str = ' && '.join(condition)
            if condition_str not in condition_set:
                yield condition_str
                condition_set.add(condition_str)
        else:
            for p in P:
                if p not in condition:
                    new_condition = condition + [p]
                    if len(new_condition) == 1:
                        yield from generate_condition(k - 1, new_condition)
                    elif len(new_condition) > 1:
                        new_condition.sort()
                        new_condition_str = new_condition[0] + " " + random.choice(C) + " "
                        for i in range(1, len(new_condition) - 1):
                            new_condition_str += new_condition[i] + " " + random.choice(C) + " "
                        new_condition_str += new_condition[-1]
                        complexity = len(new_condition_str.split())
                        if complexity <= max_k:
                            yield from generate_condition(k - 1, [new_condition_str])

    for k in range(1, max_k + 1):
        yield from generate_condition(k, [])

def generate_negated(input_list, max_k):
    for input_str in input_list:
        atomic_props = input_str.split(' && ')
        for combo in itertools.product(['', '!'], repeat=len(atomic_props)):
            negated_props = [f'{combo[i]}{atomic_props[i]}' for i in range(len(atomic_props))]
            new_str = ' && '.join(negated_props)
            complexity = len(new_str.split())
            if "!" in new_str:
                complexity += 1
            if complexity <= max_k:
                yield new_str


def generate_strategies(cartesian_products, k, agents, found_solution):
    strategies = [list() for _ in range(len(agents))]  # Le strategie sono liste

    def search_solution(strategies, current_strategy, depth):
        if depth == len(agents):
            yield current_strategy
        else:
            for agent in strategies[depth]:
                current_strategy.append(agent)
                yield from search_solution(strategies, current_strategy, depth + 1)
                current_strategy.pop()

    if not found_solution:
        for index, agent_key in enumerate(cartesian_products):
            cartesian_product = cartesian_products[agent_key]

            # Generate combinations of all conditions length to reach the desired complexity bound
            for r in range(1, k + 1):
                combinations = itertools.combinations(cartesian_product, r)
                filtered_combinations = [combination for combination in combinations
                                         if len(set(action for _, action in combination)) == r  #equal to r ensures the number of different actions to be reached
                                         ]
                for combination in filtered_combinations:
                    total_complexity = sum(
                        len(condition.split()) + (1 if "!" in condition else 0) for condition, _ in combination)
                    if total_complexity == k:
                        new_strategy = {"condition_action_pairs": list(combination)}
                        if not is_duplicate(strategies[index], new_strategy):
                            strategies[index].append(new_strategy)
                            yield from search_solution(strategies, [], 0)

    return strategies


def is_duplicate(existing_dictionaries, new_dictionary):
    for existing_dictionary in existing_dictionaries:
        if existing_dictionary['condition_action_pairs'] == new_dictionary['condition_action_pairs']:
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
    cgs = CGS()
    cgs.read_file(filename)

    #For testing only: randomize formula REMOVE THE COMMENTS FROM THE CURRENT TO THE NEXT 4 ROWS USE A RANDOMIZED FORMULA AT EACH EXECUTION
    #randomized_formula = randomize_natatl_formula(formula, get_number_of_agents(), get_atomic_prop())
    #with open(f'C:\\Users\\utente\\Desktop\\Tesi\\TESTING\\Exists next with n agents\\testing11\\modified_formula.txt','w') as f:
     #   f.write(str(randomized_formula))
    #print(randomized_formula)

    #check if input model is correct
    cgs.matrixParser(cgs.get_number_of_agents())
    #transform natATL formula into CTL formula
    CTLformula = natatl_to_ctl(formula)
    print(formula)
    print(CTLformula)
    k = get_k_value(formula)

    agents = get_agents_from_natatl(formula)
    print(f"Envolved agents: {agents}")
    actions_per_agent = cgs.get_actions(agents)
    print(f"actions picked by each agent:{actions_per_agent}")
    agent_actions = {}
    for i, agent_key in enumerate(actions_per_agent.keys()):
        agent_actions[f"actions_{agent_key}"] = actions_per_agent[agent_key]
    #print(f"Obtained actions: {agent_actions}")
    actions_list = [actions for actions in agent_actions.values()]
    atomic_propositions = cgs.get_atomic_prop()
    print(atomic_propositions)
    return k, agent_actions, actions_list, atomic_propositions, CTLformula, agents, cgs

def generate_cartesian_products(actions_list, conditions):
    cartesian_products = {}
    for i, actions in enumerate(actions_list, start=1):
        agent_key = f"actions_agent{i}"
        agent_cartesian_product = list(itertools.product(conditions, actions))
        if agent_key not in cartesian_products:
            cartesian_products[agent_key] = []
        cartesian_products[agent_key].extend(agent_cartesian_product)
    return cartesian_products

def generate_guarded_action_pairs(k, agent_actions, actions_list, atomic_propositions):
    C = ['and', 'or']
    try:
        cartesian_products = {}
        for agent_key in agent_actions.keys():
            conditions = list(generate_conditions(atomic_propositions, C, k))
            for condition in conditions:
                negated_conditions = list(generate_negated([condition], k))
                all_conditions = [condition] + negated_conditions
                new_cartesian_products = generate_cartesian_products(actions_list, all_conditions)
                for key, value in new_cartesian_products.items():
                    if key not in cartesian_products:
                        cartesian_products[key] = []
                    cartesian_products[key].extend(value)
        return cartesian_products

    except Exception as e:
        print(f"An error occurred: {e}")
        return {}


