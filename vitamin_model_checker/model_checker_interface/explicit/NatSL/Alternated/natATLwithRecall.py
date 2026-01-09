from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.strategies import initialize, generate_guarded_action_pairs, create_reg_exp, generate_strategies
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.pruning import pruning
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.tree import build_tree_from_CGS
import time
import copy


def existentialNatATL(model, ex_formula, un_formula, start_time):
    """
    Funzione che implementa il ciclo di generazione delle strategie esistenziali
    e verifica se soddisfano la formula NatATL. Se una strategia esistenziale non è valida,
    si passa al controllo contro tutte le strategie universali.
    """

    # Inizializza il modello
    k, agent_actions, actions_list, atomic_propositions, CTLformula, agents, filename, cgs = initialize(model, ex_formula)
    height = 3  # Altezza massima dell'albero per il pruning
    found_solution = False  # Flag per verificare se è stata trovata una soluzione
    i = 1  # Livello iniziale per la generazione delle strategie

    # Loop principale per la generazione delle strategie esistenziali
    while not found_solution and i <= k:
        print(f"Generating existential strategies with depth {i}...")

        # Costruzione dell'albero per la strategia esistenziale
        tree = build_tree_from_CGS(cgs, cgs.get_states(), height)

        # Generazione delle espressioni regolari e combinazioni di azioni
        reg_exp = create_reg_exp(i, atomic_propositions)
        cartesian_products = generate_guarded_action_pairs(list(reg_exp), list(actions_list))
        strategies_iterator = generate_strategies(cartesian_products, i, agents, found_solution)

        # Iterazione sulle strategie generate
        for collective_strategy in strategies_iterator:
            print(f"Testing existential strategy: {collective_strategy}")

            # Copia dell'albero per la strategia corrente
            tree_copy = copy.deepcopy(tree)

            # Applica il pruning con la strategia corrente
            if pruning(cgs, tree_copy, height, filename, CTLformula, *collective_strategy):
                print(f"Solution found for existential agents: {collective_strategy}")
                end_time = time.time()
                print(f"Elapsed time is {end_time - start_time} seconds.")
                found_solution = True
                break  # Esci dal ciclo se la soluzione è valida
            else:
                # La strategia non è valida, passa alla validazione universale
                print(f"Checking universal strategies against existential strategy: {collective_strategy}")
                valid = universalNatATL(tree_copy, model, un_formula,1,height)

                if valid:
                    print("Solution is valid against all universal strategies.")
                    found_solution = True
                    break  # Esci dal ciclo se la soluzione è valida
                else:
                    print(f"Current existential strategy {collective_strategy} is invalid. Moving to the next.")

        # Incrementa la profondità per la generazione delle strategie successive
        i += 1

    # Messaggio finale se nessuna soluzione è stata trovata
    if not found_solution:
        print("No solution found for the given NatATL formula.")

    return found_solution


def universalNatATL(tree, model, formula, num_agents, height):
    if num_agents == 0:
        print("No universal agents. Ending process.")
        return False
    solution = True
    i = 1
    k, agent_actions, actions_list, atomic_propositions, CTLformula, agents, filename, cgs = initialize(model, formula)

    while solution and i <= k:
    #start_time = time.time()
        print(f"STO NEL WHILE DELL' UNI")
        # Inizializza parametri per l'albero corrente
        reg_exp = create_reg_exp(i, atomic_propositions)
        conditions = list(reg_exp)
        actions = list(actions_list)
        cartesian_products = generate_guarded_action_pairs(conditions, actions)
        print(f"cartesian prods {cartesian_products}")
        strategies_iterator = generate_strategies(cartesian_products, i, agents, False)

        # Genera e verifica tutte le strategie universali
        for universal_strategy in strategies_iterator:
            print(f"Checking universal strategy: {universal_strategy}")
            if not pruning(cgs, tree, height, filename, CTLformula, *universal_strategy):
                print(f"Universal strategy {universal_strategy} invalidates current existential strategy.")
                solution = False
                break
        i += 1

    else:
        if not solution:
            #print(f"No Universal Solution found")
            return False



    return True  # Tutte le strategie universali hanno confermato quella esistenziale


