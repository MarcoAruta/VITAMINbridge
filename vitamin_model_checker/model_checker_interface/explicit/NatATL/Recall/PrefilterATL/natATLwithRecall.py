from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.strategies import initialize, generate_guarded_action_pairs, create_reg_exp, generate_strategies
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.pruning import pruning
from vitamin_model_checker.models.CGS import *
cgs = CGS()
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.tree import build_tree_from_CGS
from vitamin_model_checker.logics.ATL.parser import do_parsing
from vitamin_model_checker.model_checker_interface.explicit.ATL.ATL import model_checking
from vitamin_model_checker.model_checker_interface.explicit.NatATL.NatATLtoATL import natatl_to_atl
import time
import os
import copy


def preprocess_and_verify(model, formula):
    res={}
    start_time = time.time()
    if not os.path.isfile(model):
        raise FileNotFoundError(f"No such file or directory: {model}")
    print(f"natatl: {formula}")
    atlformula = natatl_to_atl(formula)
    print(f"atl: {atlformula}")
    cgs.read_file(model)
    res_parsing = do_parsing(atlformula, cgs.get_number_of_agents())
    print(res_parsing)

    result = model_checking(atlformula, model)
    print(result)

    if result['initial_state'] == 'Initial state s0: True':
        print("Initial state s0 è True. Avvio process_data...")
        res = natATLwithRecall(model, formula)
    else:
        print("Initial state s0 NON è True. Terminazione.")
        res["Satisfiability"] = False


    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time is {elapsed_time} seconds.")
    return res

def natATLwithRecall(model, formula):
    start_time = time.time()
    found_solution = False
    result ={}
    k, agent_actions, actions_list, atomic_propositions, CTLformula, agents, filename, cgs = initialize(model, formula)
    i = 1
    height = 4

    while not found_solution and i <= k:
        print(f"cgs {cgs}")
        tree = build_tree_from_CGS(cgs, cgs.get_states(), height)
        print("Initial Tree built from input model:")
        print(tree)
        reg_exp = create_reg_exp(i, atomic_propositions)
        conditions = list(reg_exp)
        actions = list(actions_list)
        cartesian_products = generate_guarded_action_pairs(conditions, actions)
        print(f"cartesian prods {cartesian_products}")

        strategies_iterator = generate_strategies(cartesian_products, i, agents, found_solution)

        for collective_strategy in strategies_iterator:
            print(f"check this strategy set for agents {collective_strategy}")
            tree_copy = copy.deepcopy(tree)

            if pruning(cgs, tree_copy, height, filename, CTLformula, *collective_strategy):
                print(f"Solution found {collective_strategy}")
                found_solution = True
                result['Satisfiability'] = found_solution
                result['Complexity Bound'] = i
                result['Winning Strategy per agent'] = collective_strategy
                break

        i += 1

    else:
        if not found_solution:
            print("No Solution found")
            result['Satisfiability'] = False
            result['Complexity Bound'] = k

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time is {elapsed_time} seconds.")
    return result

