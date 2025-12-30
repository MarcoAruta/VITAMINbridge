import numpy as np

class CGS():
    def __init__(self):
        # sezioni standard
        self.graph = []
        self.states = []
        self.atomic_propositions = []
        self.matrix_prop = []
        self.initial_state = ''
        self.number_of_agents = 0
        self.actions = []
        # nuove sezioni
        self.resource = 0
        self.actions_costs = []


    def read_file(self, filename):
        with open(filename, 'r') as f:
            lines = f.readlines()

        self.graph = []
        self.states = []
        self.atomic_propositions = []
        self.matrix_prop = []
        self.initial_state = ''
        self.number_of_agents = ''
        self.actions = []
        self.resource = 0
        self.actions_costs = []

        current_section = None
        transition_content = ''
        unknown_transition_content = ''
        name_state_content = ''
        atomic_propositions_content = ''
        labelling_content = ''
        rows_graph = []
        rows_prop = []

        for raw in lines:
            line = raw.rstrip('\n')
            # header sezioni
            line = line.strip()
            # Section "header"
            if line == 'Transition':
                current_section = 'Transition'
                continue
            elif line == 'Unkown_Transition_by':
                current_section = 'Unknown_Transition_by'
                continue
            elif line == 'Name_State':
                current_section = 'Name_State'
                continue
            elif line == 'Initial_State':
                current_section = 'Initial_State'
                continue
            elif line == 'Atomic_propositions':
                current_section = 'Atomic_propositions'
                continue
            elif line == 'Labelling':
                current_section = 'Labelling'
                continue
            elif line == 'Number_of_agents':
                current_section = 'Number_of_agents'
                continue
            elif line == 'Resource':
                current_section = 'Resource'
                continue
            elif line == 'Actions_Costs_from_Transition':
                current_section = 'Actions_Costs_from_Transition'
                continue

            #If not header, then read contents based on what section we are in

            if current_section == 'Transition':
                transition_content += line + '\n'
                vals = line.split()
                rows_graph.append(vals)
            elif current_section == 'Unknown_Transition_by':
                unknown_transition_content += line + '\n'
            elif current_section == 'Name_State':
                name_state_content += line + '\n'
                self.states = np.array(line.split())
            elif current_section == 'Initial_State':
                self.initial_state = line
            elif current_section == 'Atomic_propositions':
                atomic_propositions_content += line + '\n'
                self.atomic_propositions = np.array(line.split())
            elif current_section == 'Labelling':
                labelling_content += line + '\n'
                rows_prop.append(line.split())
            elif current_section == 'Number_of_agents':
                self.number_of_agents = int(line)
            elif current_section == 'Resource':
                self.resource = int(line)
            elif current_section == 'Actions_Costs_from_Transition':
                # es. "00 23,21 13,11 03"
                self.actions_costs.append(line.split())

        # costruisco self.graph da rows_graph
        for row in rows_graph:
            new_row = []
            for cell in row:
                if cell == '0':
                    new_row.append(0)
                else:
                    new_row.append(cell)
                # (estrazione self.actions se la usi da get_actions preesistente)
            self.graph.append(new_row)

        # costruisco matrix_prop da rows_prop
        for row in rows_prop:
            new_row = []
            for cell in row:
                if cell in ('0','1'):
                    new_row.append(int(cell))
                else:
                    new_row.append(cell)
            self.matrix_prop.append(new_row)

    # --- GETTERS STANDARD ---
    def get_resource(self):
        """Restituisce il valore intero di Resource."""
        return self.resource

    def get_number_of_agents(self):
        return int(self.number_of_agents)

    def get_graph(self):
        return self.graph

    def get_states(self):
        return self.states

    def get_matrix_proposition(self):
        return self.matrix_prop

    def get_number_of_states(self):
        return len(self.states)

    def get_atomic_prop(self):
        return self.atomic_propositions

    def get_initial_state(self):
        return self.initial_state

    def get_actions(self):
        return self.actions

    def translate_action_and_state_to_key(self, action_string, state):
        return action_string + ";" + state

    def get_actions(self, agents):
        # Convert the graph string to a list of lists
        graph_list = self.graph

        # Create a dictionary to store actions for each agent
        actions_per_agent = {f"agent{agent}": [] for agent in agents}

        for row in graph_list:
            for elem in row:
                if elem != 0 and elem != '*':
                    actions = elem.split(',')
                    for action in actions:
                        for i, agent in enumerate(agents):
                            if action[agent - 1] != 'I':  # idle condition
                                actions_per_agent[f"agent{agent}"].append(action[agent - 1])

        # Remove duplicates from each agent's action list
        for agent_key in actions_per_agent:
            actions_per_agent[agent_key] = list(set(actions_per_agent[agent_key]))

        return actions_per_agent

    # return the number of actions extracted in get_actions()
    def get_number_of_actions(self):

        n = self.get_actions()
        return len(n)

    def write_updated_file(self, input_filename, modified_graph, output_filename):
        if modified_graph is None:
            raise ValueError("modified_graph is None")
        with open(input_filename, 'r') as input_file, open(output_filename, 'w') as output_file:
            current_section = None
            matrix_row = 0
            for line in input_file:
                line = line.strip()

                if line == 'Transition':
                    current_section = 'Transition'
                    output_file.write(line + '\n')
                elif current_section == 'Transition' and matrix_row < len(modified_graph):
                    output_file.write(' '.join([str(elem) for elem in modified_graph[matrix_row]]) + '\n')
                    matrix_row += 1
                elif current_section == 'Transition' and matrix_row == len(modified_graph):
                    current_section = None
                    output_file.write('Unkown_Transition_by' + '\n')
                else:
                    output_file.write(line + '\n')

    # returns the edges of a graph
    def get_edges(self):
        graph = self.get_graph()
        states = self.get_states()
        # duplicate edges (double transactions from "a" to "b") are ignored due to model checking
        edges = []
        for i, row in enumerate(graph):
            for j, element in enumerate(row):
                if element == '*':
                    edges.append((states[i], states[i]))
                elif element != 0:
                    edges.append((states[i], states[j]))
        return edges

    def file_to_string(self, filename):
        with open(filename, 'r') as file:
            data = file.read()
        return data

        # returns the index of the given atom, in the array of atomic propositions
    def get_atom_index(self, element):
        array = self.get_atomic_prop()
        try:
            index = np.where(array == element)[0][0]
            return index
        except IndexError:
            print("Element not found in array.")
            return None

    # returns the index, given a state name
    def get_index_by_state_name(self, state):
        state_list = self.get_states()
        index = np.where(state_list == state)[0][0]
        return index

    # returns the state, given an index
    def get_state_name_by_index(self, index):
        states = self.get_states()
        return states[index]

    # converts action_string into a list
    def build_list(self, action_string):
        ris = ''
        if action_string == '*':
            for i in range(0, self.get_number_of_agents()):
                ris += '*'
            action_string = ris
        action_list = action_string.split(',')
        return action_list

    # returns a set of agents given a coalition (e.g. 1,2,3)
    def get_agents_from_coalition(self, coalition):
        agents = coalition.split(",")
        return set(agents)

    # sort and remove 0 from agents
    def format_agents(self, agents):
        agents = sorted(agents)
        if 0 in agents:
            agents.remove(0)
        agents = {int(x) - 1 for x in agents}
        return agents

    # returns coalition's actions
    def get_coalition_action(self, actions, agents):
        coalition_moves = set()
        result = ''
        agents = self.format_agents(agents)
        if len(agents) == 0:
            for i in range(0, self.get_number_of_agents()):
                result += '-'
        else:
            for x in actions:
                div = 1
                # if len(x) > 4:
                #     div = int(len(x) / 4)
                letter_backup = ''
                count = 1
                j = 0
                for _, letter in enumerate(x):
                    if count == div:
                        if j in agents:
                            result += letter if not letter_backup else letter_backup + letter
                        else:
                            result += '-'
                        j += 1
                        count = 1
                        letter_backup = ''
                    else:
                        letter_backup += letter
                        count += 1

                coalition_moves.add(result)
        return coalition_moves

    def get_base_action(self, action, agents):
        return self.get_coalition_action(set([action]), agents).pop()

    # returns all moves except for those of the considered coalition
    def get_opponent_moves(self, actions, agents):
        other_moves = set()
        agents = self.format_agents(agents)
        for x in actions:
            result = ""
            div = 1
            # if len(x) > 4:
            #     div = int(len(x) / 4)
            letter_backup = ''
            count = 1
            j = 0
            for i, letter in enumerate(x):
                if count == div:
                    if j not in agents:
                        result += letter if not letter_backup else letter_backup + letter
                    else:
                        result += '-'
                    j += 1
                    count = 1
                    letter_backup = ''
                else:
                    letter_backup += letter
                    count += 1
            other_moves.add(result)
        return other_moves

    # added NatATL functions below

    def update_cgs_file(self, input_file, modified_file, tree, tree_states, unwinded_CGS):
        def read_input_file(file_path):
            with open(file_path, 'r') as file:
                lines = file.readlines()
            return lines

        def write_output_file(file_path, lines):
            with open(file_path, 'w') as file:
                file.writelines(lines)

        def update_transitions(lines, new_transitions):
            transition_start = lines.index("Transition\n") + 1
            transition_end = lines.index("Unkown_Transition_by\n")
            updated_lines = lines[:transition_start] + new_transitions + lines[transition_end:]
            return updated_lines

        def update_name_state(lines, states):
            name_state_start = lines.index("Name_State\n") + 1
            initial_state_index = lines.index("Initial_State\n")
            states_line = " ".join(states) + "\n"
            updated_lines = lines[:name_state_start] + [states_line] + lines[initial_state_index:]
            return updated_lines

        def update_labelling(lines, labelling):
            labelling_start = lines.index("Labelling\n") + 1
            num_agents_index = lines.index("Number_of_agents\n")
            updated_lines = lines[:labelling_start] + labelling + lines[num_agents_index:]
            return updated_lines

        # Lettura del file di input
        lines = read_input_file(input_file)

        # Formattazione delle transizioni come richiesto
        new_transitions = []
        for row in unwinded_CGS:
            new_transitions.append(" ".join(map(str, row)) + "\n")

        # Aggiornamento delle transizioni nel file
        lines = update_transitions(lines, new_transitions)

        # Aggiornamento della lista degli stati nel file
        lines = update_name_state(lines, tree_states)

        # Creazione delle label rows dall'albero
        labelling = []

        def traverse_and_collect_labels(node):
            labelling.append(" ".join(map(str, node.label_row)) + "\n")
            for child in node.children:
                traverse_and_collect_labels(child)

        traverse_and_collect_labels(tree)

        # Aggiornamento delle label rows nel file
        lines = update_labelling(lines, labelling)

        # Scrittura del file di output aggiornato
        write_output_file(modified_file, lines)

    def get_label(self, index):
        return f's{index}'

    def create_label_matrix(self, graph):
        label_matrix = []
        for i, row in enumerate(graph):
            label_row = [self.get_label(i) if isinstance(elem, str) and elem != '*' else None for elem in row]
            label_matrix.append(label_row)
        return label_matrix

    # Validate transition matrix
    # Use Example
    # matrix = [['III', 0, 0, 0], [0, 'IIZ', 'ADZ,BDZ', 'ACZ,BCI'], ['ACZ,BDZ', 'ICZ', 'III', 'ADZ,BCZ'], [0, 'CIZ', 0, 'III']]
    # n = 3
    # parser(matrix, n)
    def matrixParser(self, n):
        for row in self.graph:
            if all(elem == 0 for elem in row):
                raise ValueError("All row elements are 0")

            char_I_count = [0] * n

            for elem in row:
                if elem == 0:
                    continue

                strings = str(elem).split(',')
                for s in strings:
                    # if len(s) != n:
                    #    raise ValueError(f"string length {s} for element {elem} is not equal to {n}")

                    for i in range(n):
                        if s[i] == 'I':
                            char_I_count[i] += 1

            if any(count == 0 for count in char_I_count):
                raise ValueError("Idle error: There has to be at least one 'I' for each row")
    def get_action_cost(self, action_letter, agent_index):
        """
        Restituisce il costo dell'azione singola `action_letter` per l'agente `agent_index` (1-based).
        Cerca nella self.graph la cella i,j in cui, per qualche tupla di azioni come "AC,BD",
        la lettera in posizione agent_index-1 sia proprio action_letter, e poi legge lo stesso
        entry in self.actions_costs per recuperare il carattere numerico corrispondente.
        """
        if agent_index < 1 or agent_index > self.number_of_agents:
            raise IndexError("agent_index deve essere tra 1 e Number_of_agents")

        for i, row in enumerate(self.graph):
            for j, cell in enumerate(row):
                if cell != 0 and cell != '*':
                    # cell può contenere più joint‐action es. "AC,BD"
                    for joint in cell.split(','):
                        # se la lettera alla posizione dell'agente è quella cercata...
                        if len(joint) >= agent_index and joint[agent_index-1] == action_letter:
                            entry = self.actions_costs[i][j]  # es. "23"
                            return int(entry[agent_index-1])

        raise ValueError(f"Azione letterale '{action_letter}' non trovata per agente {agent_index}")

    def validate_strategy(self, s_A):
        """
        Controlla per ogni agente i-esimo in s_A che
        la somma dei costi delle azioni nella lista
        'condition_action_pairs' non superi self.resource.

        s_A: list of dict, length = number_of_agents,
             each dict has key 'condition_action_pairs'
             with a list of tuples (condition, action_letter).
        Ritorna:
          True se TUTTI gli agenti rispettano il budget,
          False altrimenti.
        """
        # itero su ciascun agente
        for idx, agent_strat in enumerate(s_A):
            agent_index = idx + 1
            total_cost = 0

            for cond, action_letter in agent_strat.get('condition_action_pairs', []):
                # sommo il costo di ogni singola azione
                cost = self.get_action_cost(action_letter, agent_index)
                total_cost += cost

            if total_cost > self.resource:
                # fallisce il vincolo per questo agente
                return False

        # tutti gli agenti stanno entro budget
            print(f"{total_cost} costo totale azioni agente agent:{agent_index}")
        return True

# --- TEST RAPIDO ---
if __name__ == "__main__":
    cgs = CGS()
    cgs.read_file('C:\\Users\\utente\\Desktop\\Lavoro\\KR\\ActionsResourceModel.txt')
    print("Resource:", cgs.get_resource())
    # es. costi per l'azione "AC" (prima apparizione) per entrambi gli agenti:
    print("Costo di 'A' per agente 1:", cgs.get_action_cost("A", 1))
    print("Costo di 'D' per agente 2:", cgs.get_action_cost("D", 2))
    s_A = [
        {'condition_action_pairs': [('a', 'A'), ('a', 'B')]},  # agente 1
        {'condition_action_pairs': [('a', 'C'), ('a', 'D')]}  # agente 2
    ]

    valid = cgs.validate_strategy(s_A)
    print("Strategia valida?", valid)