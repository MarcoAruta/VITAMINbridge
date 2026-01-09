from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.strategies import initialize, generate_guarded_action_pairs, create_reg_exp, generate_strategies
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.pruning import pruning
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.tree import build_tree_from_CGS
import time
import copy

def existentialNatATL(model, formula):
    found_solution = False
    k, agent_actions, actions_list, atomic_propositions, CTLformula, agents, filename, cgs = initialize(model, formula)
    i = 1
    height = 3
    # CONSIDERAZIONI SULL'ALTEZZA:
    # 11 NON GENERA L'ALBERO DOPO >15 MINUTI, SERVE UN ALTEZZA BUONA MA RT
    # 7 FUNZIONA MA PERDE QUALCHE SECONDO (4-5 AI 5-10) PER LA GENERAZIONE DELL'ALBERO
    # 6 IMPIEGA 4 SECONDI TRA UNA GENERAZIONE DI UN ALBERO E L'ALTRA
    # fino a 5: RT

    pruned_trees = []  # Struttura dati per memorizzare gli alberi prunati

    while not found_solution and i <= k:
        print(f"cgs {cgs}")
        tree = build_tree_from_CGS(cgs, cgs.get_states(), height)  # Sostituisci altezza con #n di stati
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
            tree_copy = copy.deepcopy(tree)  # Crea una copia profonda dell'albero
            if pruning(cgs, tree_copy, height, filename, CTLformula, *collective_strategy):
                print(f"Solution found {collective_strategy}")
                found_solution = True
                break
            pruned_trees.append(tree_copy)  # Memorizza l'albero prunato

        i += 1
    else:
        if not found_solution:
            print(f"No Solution found")




    return found_solution, pruned_trees, height,cgs  # Ritorna la lista degli alberi prunati


def universalNatATL(trees, model, formula, states, num_agents, height, start_time):
    # Se non ci sono agenti universali, termina immediatamente
    if num_agents == 0:
        print("No universal agents to generate strategies. Ending process.")
        return False

    # Inizializza il tempo di inizio
    found_solution = False
    i = 1

    # Itera su ogni albero prunato nella lista
    for tree_index, tree in enumerate(trees):
        print(f"Processing tree {tree_index + 1}/{len(trees)}")

        # Inizializza i parametri del modello
        k, agent_actions, actions_list, atomic_propositions, CTLformula, agents, filename, cgs = initialize(model, formula)

        #Converti l'albero in un modello utilizzabile
        #cgs = tree_to_initial_CGS(tree, states, num_agents, height)
        #print(f"cgs riottenuta: {cgs}")

        reg_exp = create_reg_exp(k, atomic_propositions)
        conditions = list(reg_exp)
        actions = list(actions_list)
        cartesian_products = generate_guarded_action_pairs(conditions, actions)

        # Genera strategie universali
        strategies_iterator = generate_strategies(cartesian_products, k, agents, found_solution)

        # Itera su ogni strategia generata
        for collective_strategy in strategies_iterator:
            print(f"Checking universal strategy: {collective_strategy}")

            # Crea una copia profonda dell'albero per il pruning
            tree_copy = copy.deepcopy(tree)
            print(f"Collective strategy: {collective_strategy}")
            if pruning(cgs, tree_copy, height, filename, CTLformula, *collective_strategy):
                # Controlla il risultato del model checking
                print(f"Strategy valid for tree {tree_index + 1}, moving to next strategy.")
            else:
                print("Model checking failed, moving to next tree.")
                break  # Passa al prossimo albero

        else:
            # Se tutte le strategie sono state validate senza fallire, abbiamo trovato una soluzione
            print(f"Universal solution found with tree {tree_index + 1}.")
            found_solution = True
            break

    if not found_solution:
        print("No universal solution found.")

    # Fine del timer
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time for universalNatATL is {elapsed_time} seconds.")

    return found_solution





