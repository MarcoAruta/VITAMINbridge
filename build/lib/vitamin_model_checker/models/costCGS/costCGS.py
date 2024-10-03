import numpy as np
from vitamin_model_checker.models.CGS.CGS import CGS

class costCGS(CGS):
    def init(self):
        super(costCGS, self).init()
        self.costs = []
        self.cost_for_action = {}
        self.usesCostsInsteadOfActions = False


    def read_file(self, filename):
        with open(filename, 'r') as f:
            lines = f.readlines()

        self.graph = []
        self.states = []
        self.atomic_propositions = []
        self.matrix_prop = []
        self.initial_state = ''
        self.number_of_agents = ''
        self.cost_for_action = {}
        self.usesCostsInsteadOfActions = False

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
            elif line == 'Transition_With_Costs':
                current_section = 'Transition'
                self.usesCostsInsteadOfActions = True
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
            elif line == 'Costs_for_actions':
                current_section = 'Costs_for_actions'
            elif line == 'Costs_for_actions_split':
                current_section = 'Costs_for_actions_split'

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
            elif current_section == "Costs_for_actions":
                values = line.strip().split()
                action_name = values[0]
                state_and_cost_string = values[1].split(";")
                for couple in state_and_cost_string:
                    state_and_cost = couple.split("$")
                    costs = [int(c) for c in state_and_cost[1].split(':')]
                    self.cost_for_action.update({self.translate_action_and_state_to_key(action_name, state_and_cost[0]): costs})
            elif current_section == "Costs_for_actions_split":
                values = line.strip().split()
                action_name = values[0]
                state_and_cost_string = values[1].split(";")
                for couple in state_and_cost_string:
                    state_and_cost = couple.split("$")
                    costs_res = state_and_cost[1].split(':')
                    costs = [[int(cc) for cc in c.split(',')] for c in costs_res]
                    self.cost_for_action.update({self.translate_action_and_state_to_key(action_name, state_and_cost[0]): costs})
        
        actions =[]
        a = 0
        grafo_prov = np.array(rows_graph)
        for row in grafo_prov:
            new_row = []
            for item in row:
                if item == '0':
                    new_row.append(0)
                else:
                    if (self.usesCostsInsteadOfActions):
                        new_row.append(item)
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
        super(costCGS, self).read_from_model_object(model)
        self.capacities_assignment = model.capacities_assignment
        self.action_capacities = model.actions_for_capacities
        self.capacities = np.array(model.capacities)
        self.cost_for_action = model.cost_for_action
        
    def get_cost_for_action(self, action, state):
        return self.cost_for_action[self.translate_action_and_state_to_key(action, state)]
        
    def get_cost_for_action_all(self):
        return self.cost_for_action