from vitamin_model_checker.model_checker_interface.explicit.LTL.pruning import pruning
from vitamin_model_checker.model_checker_interface.explicit.LTL.strategies import generate_deviations_for_agent


def isNotNash(model, cgs, agents, CTLformula, current_strategy, bound, agent_actions, atomic_propositions):
    """
    Data una strategia collettiva corrente, itera sugli agenti e verifica se per almeno uno di essi esiste
    una deviazione unilaterale che, sostituendo la strategia individuale corrente in current_strategy, porta
    a un outcome favorevole (verificato da pruning()).
    """
    for agent_index, agent in enumerate(agents):
        print(f"Agente {agent_index}: {agent}")
        print(f"Strategia corrente passata a pruning: {current_strategy}")
        if not pruning(cgs, model, agents, CTLformula, current_strategy):
            agent_key = f"actions_agent{agent}"
            agent_actions_for_agent = agent_actions.get(agent_key, [])
            print(f"comunque ci sono {agents} con {enumerate(agents)}")
            print(f"Azioni disponibili per l'agente {agent}: {agent_actions_for_agent}")
            deviations = generate_deviations_for_agent(
                current_strategy[agent_index],
                bound,
                agent_actions_for_agent,
                atomic_propositions
            )
            for deviation in deviations:
                original_strategy = current_strategy[agent_index]
                current_strategy[agent_index] = deviation
                print(f"Strategia modificata per agente {agent}: {current_strategy}")
                if pruning(cgs, model, agents, CTLformula, current_strategy):
                    print(f"Deviazione trovata per l'agente {agent}: {deviation}")
                    return True
                current_strategy[agent_index] = original_strategy
    return False


def existsNash(cgs, agents, CTLformula, current_strategy, i, agent_actions, atomic_propositions):
    return not isNotNash(cgs, agents, CTLformula, current_strategy, i, agent_actions, atomic_propositions)


