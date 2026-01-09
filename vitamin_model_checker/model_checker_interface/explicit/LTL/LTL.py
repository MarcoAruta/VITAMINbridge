import time
from vitamin_model_checker.model_checker_interface.explicit.SolutionConcepts.Solution_Concepts import *
from vitamin_model_checker.model_checker_interface.explicit.LTL.strategies import *
#Non presente in Solution_Concepts perchè questo algoritmo stesso è sureWin
def model_checking_sureWin(model, formula, k, agents):
    flag = 2 #sureWin flag
    start_time = time.time()
    result={}
    found_solution = False
    agent_actions, actions_list, atomic_propositions, CTLformula, agents, cgs, nash_agents = initialize(model, formula,k, agents)
    i = 1
    while not found_solution and i <= k:
        cartesian_products = generate_guarded_action_pairs(i, agent_actions, actions_list, atomic_propositions)
        strategies_generator = generate_strategies(cartesian_products, i, agents, found_solution)
        for current_strategy in strategies_generator: #deviation exploration for involved agents
            found_solution = pruning(cgs, model, agents, CTLformula, current_strategy)
            if found_solution:
                print("Solution found! It is not a Nash Equilibrium!")
                print("Satisfiable formula")
                result['Satisfiability'] = found_solution
                result['Complexity Bound'] = i
        i += 1
    else:
        if not found_solution:
            print(f"Formula does not satisfy the given model, the game brings to a Nash Equilibrium for the selected agents")
            print("Unsatisfiable formula")
            result['Satisfiability'] = False
            result['Complexity Bound'] = k
    return result


def model_checking_isNotNash(model, cgs, formula, k, natural_strategies, selected_agents):
    start_time = time.time()
    flag = 1 #per dire che sto in isNotNash
    result={}
    # Inizializza e raccoglie tutti i dati necessari
    agent_actions, actions_list, atomic_propositions, CTLformula, agents, filename, nash_agents = initialize(model, formula, k, selected_agents)
    print(f"strategie naturali create: {natural_strategies}")
    #found_solution = False

    # Se l'utente ha inserito manualmente le strategie naturali, verifichiamo con isNotNash
    if natural_strategies is not None:
        print("\nUtilizzo delle strategie naturali fornite manualmente dall'utente.")
        if isNotNash(model, cgs, selected_agents, CTLformula, natural_strategies, k, agent_actions, atomic_propositions):

            elapsed_time = time.time() - start_time
            print("Deviazione trovata: la strategia naturale NON è un Nash Equilibrium!")
            result['Satisfiability'] = False
            result['Complexity Bound'] = k
            return result
        else:
            elapsed_time = time.time() - start_time
            print("Nessuna deviazione trovata: la strategia naturale risulta essere un Nash Equilibrium!")
            result['Satisfiability'] = True
            result['Complexity Bound'] = k
            return result


def model_checking_existNash(model, formula, k, agents):
    flag = 3
    start_time = time.time()
    # Inizializza e raccoglie tutti i dati necessari
    agent_actions, actions_list, atomic_propositions, CTLformula, agents, cgs, nash_agents = initialize(model, formula, k, agents)
    found_solution = False
    result = {}
    for i in range(1, k + 1):
        cartesian_products = generate_guarded_action_pairs(i, agent_actions, actions_list, atomic_propositions)
        strategies_generator = generate_strategies(cartesian_products, i, agents, found_solution)

        # Per ogni strategia collettiva generata
        for current_strategy in strategies_generator:
            # existsNash viene usata per verificare se esiste almeno una deviazione vincente per qualche agente
            if existsNash(cgs, list(range(1, nash_agents + 1)), CTLformula, current_strategy, i, agent_actions, atomic_propositions):
                elapsed_time = time.time() - start_time
                print("Nash Equilibrium trovato!")
                found_solution = True
                result['Satisfiability'] = found_solution
                result['Complexity Bound'] = i
                return result

    elapsed_time = time.time() - start_time
    print("The game doesn't lead to a Nash Equilibrium for the selected agents")
    result['Satisfiability'] = False
    result['Complexity Bound'] = k
    return result


def model_checking_winsSomeNash(cgs, agents, CTLformula, current_strategy, bound, agent_actions, atomic_propositions, target_agent):
    """
    Verifica se esiste un profilo strategico Nash in cui l'agente target raggiunge il proprio obiettivo.

    Secondo la descrizione a pagina 5:
      1. Si "indovina" un profilo strategico sAgt (current_strategy);
      2. Se il percorso risultante (path(sAgt)) soddisfa la formula di target_agent (Φ_target)
         e se il profilo strategico è un Nash Equilibrium (ossia, non esistono deviazioni vantaggiose per alcun agente),
         allora la funzione restituisce True.


    """
    result={}
    # Controlla se il percorso (outcome) soddisfa l'obiettivo del target_agent.
    if check_agent_win(cgs, target_agent, CTLformula, current_strategy) and not isNotNash(cgs, agents, CTLformula, current_strategy, bound, agent_actions, atomic_propositions):
        result['Satisfiability'] = False
        return result
    result['Satisfiability']=True
    return result


 # Check if the agent loses in some Nash equilibrium
def check_agent_win(model, agent, CTLformula, current_strategy):
    """
    Funzione ausiliaria che verifica se il percorso derivato dal profilo strategico corrente
    soddisfa l'obiettivo (formula CTL transformed) dell'agente specificato.

    """
    return pruning(model, [agent], CTLformula, current_strategy)


def model_checking_LoseSomeNash(cgs, agents, CTLformula, current_strategy, bound, agent_actions, atomic_propositions, target_agent):

    result={}
    if not check_agent_win(cgs, target_agent, CTLformula, current_strategy) and not isNotNash(cgs, agents, CTLformula, current_strategy, bound, agent_actions, atomic_propositions):
        result['Satisfiability']=True
        return result
    result['Satisfiability'] = False
    return result