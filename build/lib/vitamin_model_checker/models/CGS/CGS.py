import numpy as np

class CGS():
    def init(self):
        self.graph = []
        self.states = []
        self.atomic_propositions = []
        self.matrix_prop = []
        self.initial_state = ''
        self.number_of_agents = ''
        self.actions = []

    def read_file(self, filename):
        with open(filename, 'r') as f:
            lines = f.readlines()

        self.graph = []
        self.states = []
        self.atomic_propositions = []
        self.matrix_prop = []
        self.initial_state = ''
        self.number_of_agents = ''

        current_section = None
        transition_content = ''
        unknown_transition_content = ''
        name_state_content = ''
        atomic_propositions_content = ''
        labelling_content = ''
        rows_graph = []
        rows_prop = []
        

        for line in lines:
            line = line.strip()
            #Section "header"
            if line == 'Transition':
                current_section = 'Transition'
            elif line == 'Unkown_Transition_by':
                current_section = 'Unknown_Transition_by'
            elif line == 'Name_State':
                current_section = 'Name_State'
            elif line == 'Initial_State':
                current_section = 'Initial_State'
            elif line == 'Atomic_propositions':
                current_section = 'Atomic_propositions'
            elif line == 'Labelling':
                current_section = 'Labelling'
            elif line == 'Number_of_agents':
                current_section = 'Number_of_agents'

            #If not header, then read contents based on what section we are in
            
            elif current_section == 'Transition':
                transition_content += line + '\n'
                values = line.strip().split()
                rows_graph.append(values)
            elif current_section == 'Unknown_Transition_by':
                unknown_transition_content += line + '\n'
            elif current_section == 'Name_State':
                name_state_content += line + '\n'
                values = line.strip().split()
                self.states = np.array(values)
            elif current_section == 'Initial_State':
                self.initial_state = line
            elif current_section == 'Atomic_propositions':
                atomic_propositions_content += line + '\n'
                values = line.strip().split()
                self.atomic_propositions = np.array(values)
            elif current_section == 'Labelling':
                labelling_content += line + '\n'
                values = line.strip().split()
                rows_prop.append(values)
            elif current_section == 'Number_of_agents':
                self.number_of_agents = line
            
        actions =[]
        a = 0
        grafo_prov = np.array(rows_graph)
        for row in grafo_prov:
            new_row = []
            for item in row:
                if item == '0':
                    new_row.append(0)
                else:
                    new_row.append(str(item))
                    a = item.split(",")
                    for elem in a :
                        actions.append(elem)
            self.graph.append(new_row)   

        matrix_prop_prov = np.array(rows_prop)
        for row in matrix_prop_prov:
            new_row = []
            for item in row:
                if item == '0':
                    new_row.append(0)
                elif item == '1':
                    new_row.append(1)
                else:
                    new_row.append(str(item))
            self.matrix_prop.append(new_row)

    def read_from_model_object(self, model):
        self.graph = model.transition_matrix
        self.states = np.array(model.state_names)
        self.atomic_propositions = np.array(model.propositions)
        self.matrix_prop = model.labelling_function
        self.initial_state = model.initial_state
        self.number_of_agents = model.number_of_agents
        self.actions = model.actions
        
    def get_graph(self):
        return self.graph

    def get_states(self):
        return self.states

    def get_atomic_prop(self):
        return self.atomic_propositions


    def get_matrix_proposition(self):
        return self.matrix_prop


    def get_initial_state(self):
        return self.initial_state


    def get_number_of_agents(self):
        return int(self.number_of_agents)

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

    #return the number of actions extracted in get_actions()
    def get_number_of_actions (self):

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

    #returns the edges of a graph
    def get_edges(self):
        graph = self.get_graph()
        states = self.get_states()
        #duplicate edges (double transactions from "a" to "b") are ignored due to model checking
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
                div = 2
                # if len(x) > 4:
                #     div = int(len(x) / 4)
                letter_backup = ''
                count = 1
                j = 0
                for _, letter in enumerate(x):
                    if count == div:
                        if j in agents:
                            result += letter if not letter_backup else letter_backup+letter
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
            div = 2
            # if len(x) > 4:
            #     div = int(len(x) / 4)
            letter_backup = ''
            count = 1
            j = 0
            for i, letter in enumerate(x):
                if count == div:
                    if j not in agents:
                        result += letter if not letter_backup else letter_backup+letter
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

    #added NatATL functions below

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
    #matrix = [['III', 0, 0, 0], [0, 'IIZ', 'ADZ,BDZ', 'ACZ,BCI'], ['ACZ,BDZ', 'ICZ', 'III', 'ADZ,BCZ'], [0, 'CIZ', 0, 'III']]
    #n = 3
    #parser(matrix, n)
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
                    #if len(s) != n:
                    #    raise ValueError(f"string length {s} for element {elem} is not equal to {n}")

                    for i in range(n):
                        if s[i] == 'I':
                            char_I_count[i] += 1

            if any(count == 0 for count in char_I_count):
                raise ValueError("Idle error: There has to be at least one 'I' for each row")