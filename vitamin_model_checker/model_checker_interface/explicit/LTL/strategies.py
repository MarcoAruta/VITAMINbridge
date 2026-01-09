import itertools
import random
from vitamin_model_checker.models.CGS import *
from vitamin_model_checker.logics.LTL.ltl_to_ctl import *
from vitamin_model_checker.logics.LTL.matrix_parser import *

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

def initialize(model_path, formula, k, agents):
    import os
    import itertools
    cgs = CGS()
    filename = os.path.abspath(model_path)
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"No such file or directory: {filename}")
    cgs.read_file(filename)
    print("Formula:", formula)

    graph = cgs.get_graph()
    matrixParser(graph, cgs.get_number_of_agents())
    CTLformula = ltl_to_ctl(formula)
    print("Formula natATL:", formula)
    print("Formula CTL:", CTLformula)

    #while True:
     #   try:
      #      k = int(input("Insert a Complexity Bound Integer value between 1 and 10: "))
       #     if 1 <= k <= 10:
        #        break
         #   else:
          #      print("Error: Complexity too high to handle! Choose between 1 and 10.")
        #except ValueError:
         #   print("Error: You have to insert an integer.")
    print(f"Complexity Bound: {k}")


    actions_per_agent = cgs.get_actions(agents)
    print(f"Actions picked by each agent: {actions_per_agent}")
    agent_actions = {}
    for i, key in enumerate(actions_per_agent.keys()):
        agent_actions[f"actions_agent{agents[i]}"] = actions_per_agent[key]
    actions_list = [actions for actions in agent_actions.values()]
    atomic_propositions = cgs.get_atomic_prop()
    print("Atomic propositions:", atomic_propositions)

    return agent_actions, actions_list, atomic_propositions, CTLformula, agents, cgs, cgs.get_number_of_agents()

def generate_cartesian_products(actions_list, conditions):
    import itertools
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


def generate_deviations_for_agent(single_strategy, k, agent_actions_for_agent, atomic_propositions):
    import itertools
    C = ['and', 'or']
    # Genera tutte le possibili condizioni usando generate_conditions()
    conditions = list(generate_conditions(atomic_propositions, C, k))
    all_candidates = []
    # Per ogni condizione, genera anche le versioni negate
    for condition in conditions:
        neg_conditions = list(generate_negated([condition], k))
        all_conditions = [condition] + neg_conditions
        for cond in all_conditions:
            for action in agent_actions_for_agent:
                candidate = (cond, action)
                # Calcola la complessità: numero di termini nella condizione, più 1 se contiene "!"
                complexity = len(cond.split()) + (1 if "!" in cond else 0)
                if complexity <= k:
                    all_candidates.append(candidate)

    deviations = []
    current_pairs = single_strategy.get("condition_action_pairs", [])
    num_pairs = len(current_pairs)
    # Genera deviazioni considerando tutte le possibili combinazioni di candidate
    # con lo stesso numero di coppie della strategia corrente
    for candidate_tuple in itertools.product(all_candidates, repeat=num_pairs):
        candidate_strategy = {"condition_action_pairs": list(candidate_tuple)}
        if candidate_strategy != single_strategy:
            # Calcola la complessità totale della strategia candidata
            total_complexity = sum(len(pair[0].split()) + (1 if "!" in pair[0] else 0) for pair in candidate_tuple)
            if total_complexity <= k:
                deviations.append(candidate_strategy)
    return deviations


def generate_single_strategy(selected_agents, k, agent_actions, actions_list, atomic_propositions):
    found_solution = False  # Inizialmente non abbiamo una soluzione già trovata
    # Genera i prodotti cartesiani (coppie condizione-azione) per ciascun agente
    cartesian_products = generate_guarded_action_pairs(k, agent_actions, actions_list, atomic_propositions)
    # Ottieni il generatore di strategie (si noti che generate_strategies restituisce una sequenza generata)
    strategy_generator = generate_strategies(cartesian_products, k, selected_agents, found_solution)
    try:
        # Restituisci la prima strategia generata
        return next(strategy_generator)
    except StopIteration:
        return None

def generate_single_strategy_random(selected_agents, k, agent_actions, atomic_propositions):
    """
    Genera una strategia naturale random per gli agenti selezionati, scegliendo una coppia (condizione, azione)
    per ciascun agente in modo casuale, e controllando che la somma delle complessità delle condizioni sia uguale a k.
    La complessità viene calcolata come il numero di parole nella condizione, incrementato di 1 se contiene "!".
    Se dopo un numero massimo di tentativi non viene trovata una strategia valida, viene restituito None.
    """
    # Prepara la lista di azioni per ciascun agente, mantenendo l'ordine di selected_agents
    actions_list = [agent_actions.get(f"agent{agent}", []) for agent in selected_agents]
    # Genera i prodotti cartesiani per tutte le coppie condizione-azione
    cartesian_products = generate_guarded_action_pairs(k, agent_actions, actions_list, atomic_propositions)
    attempts = 100  # numero massimo di tentativi
    for _ in range(attempts):
        strategy = []
        total_complexity = 0
        valid = True
        for agent in selected_agents:
            key = f"actions_agent{agent}"
            candidate_list = cartesian_products.get(key, [])
            if not candidate_list:
                valid = False
                break
            cond, act = random.choice(candidate_list)
            strategy.append((cond, act))
            # Calcola la complessità: numero di parole nella condizione + 1 se contiene il simbolo "!"
            cplx = len(cond.split())
            if "!" in cond:
                cplx += 1
            total_complexity += cplx
        if valid and total_complexity == k:
            # Restituisce la strategia nel formato atteso:
            # [{'condition_action_pairs': [(condizione, azione)]}, {...}, ...]
            return [{"condition_action_pairs": [(s[0], s[1])]} for s in strategy]
    return None


