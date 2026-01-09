from vitamin_model_checker.model_checker_interface.explicit.NatATL.Memoryless.strategies import initialize, generate_strategies, generate_guarded_action_pairs
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Memoryless.pruning import pruning
from vitamin_model_checker.models.CGS import *
from vitamin_model_checker.logics.ATL.parser import do_parsing
from vitamin_model_checker.model_checker_interface.explicit.ATL.ATL import model_checking
import time
import os
from vitamin_model_checker.model_checker_interface.explicit.NatATL.NatATLtoATL import natatl_to_atl


def preprocess_and_verify(model, formula):
    start_time = time.time()
    if not os.path.isfile(model):
        raise FileNotFoundError(f"No such file or directory: {model}")
    
    atlformula = natatl_to_atl(formula)
    print(f"atl: {atlformula}")
    cgs = CGS()
    res={}
    cgs.read_file(model)
    res_parsing = do_parsing(atlformula, cgs.get_number_of_agents())
    print(res_parsing)

    result = model_checking(atlformula, model)
    print(result)

    if result['initial_state'] == 'Initial state s0: True':
        print("Initial state s0 è True. Avvio model checking NatATL...")
        res = process_data(model, formula)
    else:
        print("Initial state s0 NON è True. Terminazione.")
        res["Satisfiability"] = False

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time is {elapsed_time} seconds.")

    return res

def process_data(structure, formula):
    start_time = time.time()
    found_solution = False
    k, agent_actions, actions_list, atomic_propositions, CTLformula, agents, cgs = initialize(structure, formula)
    i = 1
    result = {}
    while not found_solution and i <= k:
        cartesian_products = generate_guarded_action_pairs(i, agent_actions, actions_list, atomic_propositions)
        strategies_generator = generate_strategies(cartesian_products, i, agents, found_solution)
        for current_strategy in strategies_generator:
            print(f"strategy under exam: {current_strategy}")
            found_solution = pruning(cgs, structure, agents, CTLformula, current_strategy)
            if found_solution:
                print("Solution found!")
                result['Satisfiability'] = found_solution
                result['Complexity Bound'] = i
                result['Winning Strategy per agent'] = current_strategy
                break
        i += 1
    else:
        if not found_solution:
            print(f"False, no states satisfying {CTLformula} have been found!")
            result['Satisfiability'] = False
            result['Complexity Bound'] = k
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time is {elapsed_time} seconds.")

    return result

