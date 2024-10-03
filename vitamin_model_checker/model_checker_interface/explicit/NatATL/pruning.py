from vitamin_model_checker.model_checker_interface.explicit.CTL import model_checking
from vitamin_model_checker.models.CGS import *

#path destination for new updated input file
pruned_model_file = './tmp.txt'

def modify_matrix(graph, label_matrix, states, action, agent_index, agents):
    #print(f"states:{states}")
    new_graph = [row.copy() for row in graph]
    rows_modified = [False] * len(new_graph)
    for i, row in enumerate(new_graph):
        row_modified = False
        for j, elem in enumerate(row):
            if label_matrix[i][j] in states:
                if isinstance(elem, str) and elem != '*':
                    elem_parts = elem.split(',')
                    new_elem_parts = []
                    for part in elem_parts:
                        part_list = list(part)
                        agent_matches = False
                        if part_list[agents[agent_index-1]-1] == 'I' or part_list[agents[agent_index-1]-1] == action:
                            agent_matches = True
                        if agent_matches:
                            new_elem_parts.append(part)
                    new_elem = ','.join(new_elem_parts)
                    new_graph[i][j] = new_elem if new_elem else 0
                    row_modified = True
        rows_modified[i] = row_modified
    return new_graph

def process_transition_matrix_data(cgs, model, agents,  *strategies):
    graph = cgs.get_graph()
    label_matrix = cgs.create_label_matrix(graph)
    print(f"initial transition matrix: {graph}")
    #print(f"associated labelling matrix:{label_matrix}")
    actions_per_agent = cgs.get_actions(agents)
    agent_actions = {}
    for i, agent_key in enumerate(actions_per_agent.keys()):
        agent_actions[f"actions_{agent_key}"] = actions_per_agent[agent_key]

    for agent_key in agent_actions:
        print(agent_key)
        print(agent_actions[agent_key])

    for strategy_index, strategy in enumerate(strategies, start=1):
        state_sets = set()
        temp = set()
        for iteration, (condition, action) in enumerate(strategy['condition_action_pairs']):
            #print(f"condition {condition}")
            states = model_checking(condition, model)
            #print(f" result: m_checking{states}, statesres {states['res']}")
            state_set = eval(states['res'].split(': ')[1])

            if iteration > 0:
                if (state_set):
                    temp = state_sets
                    state_sets = state_set - temp
                else:
                    state_sets = set(cgs.get_states())
                    action = "I"
                #print(f"state_set: {state_sets} con iteration {iteration} action {action}")
                graph = modify_matrix(graph, label_matrix, state_sets, action, strategy_index, agents)
                #print(f"second iteration modify_matrix for agent {strategy_index}")
                print(f'new transition matrix: {graph} modified by agent {strategy_index}')
            else:
                if (state_set):
                    state_sets = state_set
                else:
                    state_sets = set(cgs.get_states())
                    action = "I"
                #print(f"state_set: {state_sets}, iteration {iteration} action {action}")
                graph = modify_matrix(graph, label_matrix, state_sets, action, strategy_index, agents)
                #print(f"First iteration of modify_matrix for agent {strategy_index}")
                print(f'new transition matrix: {graph} modified by agent {strategy_index}')

    return graph

def pruning(cgs, model, agents, formula, current_agents):
    cgs1 = CGS()
    cgs1.read_file(model)
    cgs1.graph = process_transition_matrix_data(cgs, model, agents,  *current_agents)
    cgs1.matrixParser(cgs.get_number_of_agents())
    cgs1.write_updated_file(model, cgs1.graph, pruned_model_file)
    result = model_checking(formula, pruned_model_file)

    if (result['initial_state'] == 'Initial state s0: True'):
        #print(result)
        return True