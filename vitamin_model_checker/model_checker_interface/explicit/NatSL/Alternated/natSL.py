from vitamin_model_checker.model_checker_interface.explicit.NatSL.Alternated.natATLwithRecall import existentialNatATL
import time
from vitamin_model_checker.logics.NatSL.parser import convert_natsl_to_natatl_separated


def model_checking(formula, model): #ex: E{1}xA{1}y:(x,1)(y,2)Fa
    start_time = time.time()
    result={}

    # Converte formula NatSL in NatATL
    existential_natatl, universal_natatl = convert_natsl_to_natatl_separated(formula)
    print(f"existential NatATL formula: {existential_natatl}")
    print(f"universal NatATL formula: {universal_natatl}")
    # Chiama la funzione per strategie esistenziali (strategie universali innestate internamente a existentialNatATL)
    solution = existentialNatATL(model, existential_natatl[0], universal_natatl[0], start_time)

    if not solution:
        print("No solution.")
        end_time = time.time()
        print(f"Elapsed time for universalNatATL is {end_time - start_time} seconds.")
        result['Satisfiability'] = False
    return result




