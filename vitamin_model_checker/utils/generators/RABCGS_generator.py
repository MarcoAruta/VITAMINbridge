import random
import sys

def generate_transition_matrix(num_states):
    transitions = []
    for _ in range(num_states):
        row = []
        for _ in range(num_states):
            # if random.random() < 0.3:  # Adjust the probability as needed
            #     row.append('0')
            # else:
            row.append(''.join(random.choices(['A', '^', 'B'], k=2)))
        transitions.append(row)
    return transitions

def generate_name_states(num_states):
    return ['s' + str(i) for i in range(num_states)]

def generate_initial_state(states):
    return random.choice(states)

def generate_costs_for_actions(states, transition_matrix, num_resources, num_agents):
    costs = []
    cost_dict = {}
    i = 0
    for state in states:
        for action in transition_matrix[i]:
            if action != '0':
                if action not in cost_dict:
                    cost_dict[action] = {}
                resources = []
                for _ in range(0, num_resources):
                    resources.append(','.join([str(random.randint(1, 5)) for _ in range(num_agents)]))
                cost_dict[action][state] = '$' + ':'.join(resources)
        i += 1    
    for action in cost_dict:
        costs.append(action + ' ')
        cost_str = []
        for state in cost_dict[action]:
            cost_str.append(state + cost_dict[action][state])
        costs.append(';'.join(cost_str))
        costs.append('\n')
    return costs

def generate_atomic_propositions():
    return ['p', 'q']

def generate_labelling(num_states, num_atomic_propositions):
    return [[random.randint(0, 1) for _ in range(num_atomic_propositions)] for _ in range(num_states)]

def generate_number_of_agents():
    return 2
    # return random.randint(1, 10)  # Adjust the range as needed

def generate_random_model(num_states, num_resources):
    num_agents = generate_number_of_agents()
    transition_matrix = generate_transition_matrix(num_states)
    name_states = generate_name_states(num_states)
    initial_state = generate_initial_state(name_states)
    costs_for_actions = generate_costs_for_actions(name_states, transition_matrix, num_resources, num_agents)
    atomic_propositions = generate_atomic_propositions()
    labelling = generate_labelling(num_states, len(atomic_propositions))

    model = "Transition\n{tr}".format(tr=''.join([' '.join(row) + '\n' for row in transition_matrix]))
    model += "Name_State\n{st}\n".format(st=' '.join(name_states))
    model += f"Initial_State\n{initial_state}\n"
    model += "Costs_for_actions_split\n{ct}".format(ct=''.join(costs_for_actions))
    model += f"Atomic_propositions\n{' '.join(atomic_propositions)}\n"
    model += "Labelling\n{lb}".format(lb=''.join([' '.join(map(str, row)) + '\n' for row in labelling]))
    model += f"Number_of_agents\n{num_agents}\n"

    return model

def generate_random_model_file(num_states, num_resources, filename):
    model = generate_random_model(num_states, num_resources)
    with open(filename, 'w') as f:
        f.write(model)

if __name__ == "__main__":
    num_states = max(int(sys.argv[1]), 1)
    num_resources = max(int(sys.argv[2]), 1)
    filename = sys.argv[3]
    generate_random_model_file(num_states, num_resources, filename)
    print(f"Random model with {num_states} states and {num_resources} resources generated and saved to {filename}.")
