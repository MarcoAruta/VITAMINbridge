import random
import argparse

def main():
    # Use argparse to parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate a state-transition system with agents and obstacles.")
    parser.add_argument('--agents', type=int, default=2, help='Number of agents')
    parser.add_argument('--rows', type=int, default=2, help='Number of rows in the grid')
    parser.add_argument('--columns', type=int, default=2, help='Number of columns in the grid')
    parser.add_argument('--obstacles', type=int, default=2, help='Number of obstacles in the grid')

    # Parse the arguments
    args = parser.parse_args()

    # Use parsed arguments instead of constants
    NUMBER_OF_AGENTS = args.agents
    NUMBER_OF_ROWS = args.rows
    NUMBER_OF_COLUMNS = args.columns
    NUMBER_OF_OBSTACLES = args.obstacles

    generate_random_CGS(NUMBER_OF_AGENTS, NUMBER_OF_ROWS, NUMBER_OF_COLUMNS, NUMBER_OF_OBSTACLES, 'tmp')

def generate_random_CGS(NUMBER_OF_AGENTS, NUMBER_OF_ROWS, NUMBER_OF_COLUMNS, NUMBER_OF_OBSTACLES, FILENAME):
    propositions = set()

    obstacles = set()
    while len(obstacles) != NUMBER_OF_OBSTACLES:
        obstacles.add(f'o({random.randint(2, NUMBER_OF_ROWS)},{random.randint(1, NUMBER_OF_COLUMNS)})')

    propositions.update(obstacles)

    positions = [(r, c) for r in range(1, NUMBER_OF_ROWS + 1) for c in range(1, NUMBER_OF_COLUMNS + 1)]
    agents_pos = [0] * NUMBER_OF_AGENTS
    states = []
    for _ in range((NUMBER_OF_ROWS * NUMBER_OF_COLUMNS) ** NUMBER_OF_AGENTS):
        state = set()
        for ag in range(1, NUMBER_OF_AGENTS + 1):
            state.add(f'a{ag}{positions[agents_pos[ag - 1]]}')
        for ag in state:
            pos_ag = ag[ag.index('(') + 1:-1].replace(' ', '')
            ok = True
            for obs in obstacles:
                pos_obs = obs[obs.index('(') + 1:-1].replace(' ', '')
                if pos_ag == pos_obs:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            state.update(obstacles)
            states.append(state)
            propositions.update(state)
        for i in range(NUMBER_OF_AGENTS):
            agents_pos[i] = (agents_pos[i] + 1) % len(positions)
            if agents_pos[i] != 0:
                break

    initial_state = f's{random.randint(0, len(states) - 1)}'
    states_names = ' '.join([f's{i}' for i in range(0, len(states))])
    propositions = list(propositions)
    atomic_propositions = ' '.join([prop.replace('(', '').replace(')', '').replace(',', '_').replace(' ', '') for prop in propositions])
    labelling = ''
    for state in states:
        for prop in propositions:
            if prop in state:
                labelling += '1 '
            else:
                labelling += '0 '
        labelling = labelling[:-1]
        labelling += '\n'
    labelling = labelling[:-1]
    transitions = ''
    for from_state in states:
        for to_state in states:
            if from_state == to_state:
                transitions += 'i' * NUMBER_OF_AGENTS + ' '
            else:
                transition = ''
                ok = True
                for ag in range(1, NUMBER_OF_AGENTS + 1):
                    from_pos = [prop for prop in from_state if prop.startswith(f'a{ag}')][0]
                    from_pos = [int(pos.strip()) for pos in from_pos[from_pos.index('(') + 1:-1].split(',')]
                    to_pos = [prop for prop in to_state if prop.startswith(f'a{ag}')][0]
                    to_pos = [int(pos.strip()) for pos in to_pos[to_pos.index('(') + 1:-1].split(',')]
                    diff = (from_pos[0] - to_pos[0], from_pos[1] - to_pos[1])
                    action = None
                    if diff[0] == 0 and diff[1] == 0:
                        action = 'i'
                    if diff[0] == 0 and diff[1] == 1:
                        action = 'W'
                    if diff[0] == 1 and diff[1] == 0:
                        action = 'S'
                    if diff[0] == 0 and diff[1] == -1:
                        action = 'E'
                    if diff[0] == -1 and diff[1] == 0:
                        action = 'N'
                    if not action:
                        transition = '0'
                        break
                    else:
                        transition += action
                transitions += transition + ' '
        transitions += '\n'
    transitions = transitions[:-1]
    res = f'''Transition
{transitions}
Name_State
{states_names}
Initial_State
{initial_state}
Atomic_propositions
{atomic_propositions}
Labelling
{labelling}
Number_of_agents
{NUMBER_OF_AGENTS}
'''
    with open(FILENAME, 'w') as file:
        file.write(res)

if __name__ == "__main__":
    main()
