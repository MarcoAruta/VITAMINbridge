from vitamin_model_checker.model_checker_interface.explicit.NatATL.strategies import initialize, generate_strategies, generate_guarded_action_pairs
from vitamin_model_checker.model_checker_interface.explicit.NatATL.pruning import pruning

def model_checking(formula, model):
    # Start timer
    # start_time = time.time()
    found_solution = False
    result = {}
    # initializes conditions and actions for involved agents
    k, agent_actions, actions_list, atomic_propositions, CTLformula, agents, cgs = initialize(model, formula)
    i = 1
    while not found_solution and i <= k:
        #generate guarded action pairs for each agent
        cartesian_products = generate_guarded_action_pairs(i, agent_actions, actions_list, atomic_propositions)
        # generates the initial strategies
        strategies_generator = generate_strategies(cartesian_products, i, agents, found_solution)
        # check for each strategy if there's a solution via pruning & model checking
        for current_strategy in strategies_generator:  # Iterate over the generator object
            found_solution = pruning(cgs, model, agents, CTLformula, current_strategy)  # Call pruning here
            if found_solution:
                print("Solution found!")
                found_solution = True

                # Write to file
                # with open(result, 'a') as f: #'a' to append results in the same file, 'w' to overwrite the old ones
                result['Satisfiability'] = found_solution
                result['Complexity Bound'] = i
                result['Winning Strategy per agent'] = current_strategy
                print(f"Winning Strategy per agent: {current_strategy}")
                break
        i += 1
    else:
        if (not found_solution):
            print(f"False, no states satisfying {CTLformula} have been found!")
            # with open(result, 'a') as f:
            result['Satisfiability'] = found_solution
            result['Complexity Bound'] = k

    # End timer
    # end_time = time.time()
    # elapsed_time = end_time - start_time
    # print(f"Elapsed time is {elapsed_time} seconds.")

    # # Write execution time to file
    # with open(result, 'a') as f:
    #     f.write(f"Execution time: {elapsed_time} seconds\n")
    
    return result

