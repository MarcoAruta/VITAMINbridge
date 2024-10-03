import numpy as np
from vitamin_model_checker.models.CGS.CGS import CGS

class capCGS(CGS):
    def init(self):
        super(capCGS, self).init()
        self.capacities_assignment = []
        self.action_capacities = []
        self.capacities = []


    def read_file(self, filename):
        with open(filename, 'r') as f:
            lines = f.readlines()

        self.graph = []
        self.states = []
        self.atomic_propositions = []
        self.matrix_prop = []
        self.initial_state = ''
        self.number_of_agents = ''
        self.capacities_assignment = []
        self.action_capacities = []
        self.capacities = []

        current_section = None
        transition_content = ''
        unknown_transition_content = ''
        name_state_content = ''
        atomic_propositions_content = ''
        labelling_content = ''
        rows_graph = []
        rows_prop = []
        capacities_assignment_content = ''
        action_assign_content = ''
        capacities_content = ''
        

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
            elif line == 'Capacities' :
                current_section = 'Capacities'
            elif line == 'Capacities_assignment':
                current_section = 'Capacities_assignment'
            elif line == 'Actions_for_capacities':
                current_section = 'Actions_for_capacities'

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
            elif current_section == 'Capacities' :
                capacities_content += line + '\n'
                values = line.strip().split()
                self.capacities = np.array(values)
            elif current_section == 'Capacities_assignment':
                capacities_assignment_content += line + '\n'
                values = line.strip().split()
                self.capacities_assignment.append(values)
            elif current_section == 'Actions_for_capacities':
                action_assign_content += line + '\n'
                values = line.strip().split()
                self.action_capacities.append(values)
            
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
        super(capCGS, self).read_from_model_object(model)
        self.capacities_assignment = model.capacities_assignment
        self.action_capacities = model.actions_for_capacities
        self.capacities = np.array(model.capacities)

    def get_capacities_assignment2(self):
        return self.capacities_assignment

    def get_capacities_assignment(self) :
        cap_ass = self.get_capacities_assignment2()
        result = []
        for i in range (1, self.get_number_of_agents()+1) :
            interm = [str(i)]
            cap_ag = cap_ass[i-1]
            for count, value in enumerate(cap_ag) :
                if value == '1' :
                    interm.append(self.get_capacities()[count])
            result.append(interm)

        return result


    def get_action_capacities(self):
        return self.action_capacities

    def get_capacities(self): 
        result = []
        for elem in self.capacities :
            result.append(elem)
        return result