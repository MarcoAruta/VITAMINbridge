from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.strategies import initialize, generate_guarded_action_pairs, create_reg_exp, generate_strategies
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.pruning import pruning
from vitamin_model_checker.models.CGS import *
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.tree import build_tree_from_CGS
import time
import copy



def model_checking(formula, model):
    start_time = time.time()
    found_solution = False

    k, agent_actions, actions_list, atomic_propositions, CTLformula, agents, filename, cgs = initialize(model, formula)
    i = 1
    height = 4

    result = {}

    while not found_solution and i <= k:
        print(f"cgs {cgs}")
        states = cgs.get_states()
        tree = build_tree_from_CGS(cgs, states, height)
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
            result['Satisfiability'] = found_solution
            result['Complexity Bound'] = k

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time is {elapsed_time} seconds.")

    return result

