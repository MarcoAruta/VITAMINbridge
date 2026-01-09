from vitamin_model_checker.model_checker_interface.explicit.NatSL.Sequential.natATLwithRecall import *
import time
from vitamin_model_checker.logics.NatSL.parser import normalize_formula, do_parsingNatSL, validate_bindings, extract_existential_agents, extract_universal_agents, count_universal_agents
from vitamin_model_checker.logics.NatSL.parser import convert_natsl_to_natatl_separated


def model_checking(natSLformula, model): #ex: E{1}xA{1}y:(x,1)(y,2)Fa
    result={}
    start_time = time.time()
    #Step 0: setting formule natATL da NatSL
    print(f"formula NatSL: {natSLformula}")
    #TRASFORMA QUI NATSTL FORMULA IN NATSL ESISTENZIALE E UNIVERSALE (funzione di conversione presente in natSL parser)
    existential_natatl, universal_natatl = convert_natsl_to_natatl_separated(natSLformula)
    print(f"existential NatATL formula: {existential_natatl}")
    print(f"universal NatATL formula: {universal_natatl}")
    # Normalize the formula
    flag, normalized_formula = normalize_formula(natSLformula)
    # Parse the normalized formula
    parsed = do_parsingNatSL(normalized_formula)
    if parsed:
        try:
            validate_bindings(parsed)
            print("Formula Parsata:", parsed)
            existential_agents = extract_existential_agents(parsed)
            print("Agenti Esistenziali:", existential_agents)
            universal_agents = extract_universal_agents(parsed)
            print("Agenti Universali:", universal_agents)
            n_universal = count_universal_agents(universal_agents)
            print("Numero di Agenti Universali", n_universal)
        except ValueError as e:
            print(e)
    else:
        print("Errore nel parsing della formula.")
        exit()
    #Memorizzo le formule separate in una lista per manutenibilità e future espansioni se necessario, ma passo il primo elemento come stringa sotto
    #Questo perchè il codice si aspetta una formula come stringa non come lista

    # Step 1: Chiamata alla funzione existentialNatATL
    solution, trees, height, cgs = existentialNatATL(model, existential_natatl[0])

    # Step 2: Se una soluzione esistenziale è stata trovata, termina con successo
    if solution:
        # End timer
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Elapsed time is {elapsed_time} seconds.")
        result['Satisfiability'] = solution
        return result

    # Step 3: Se non c'è soluzione esistenziale, passa alle strategie universali
    print("Switching to universal strategies.")
    result['Satisfiability'] = universalNatATL(trees, model, universal_natatl[0], cgs.get_states(), n_universal, height, start_time)
    return result
