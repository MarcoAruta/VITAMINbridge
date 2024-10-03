class p_knowledge_for_Y:

    def __init__(self, state, knowledge, beta, agents, agents_tot):
        self.state = state
        self.knowledge = knowledge
        self.action = beta 
        self.coalition = agents
        self.agents = agents_tot
    
    def print_p_knowledge_for_Y(self) :
        print(self.state)
        interm = self.agents
        if type(interm) == str:
            interm = self.agents.split(',')
        for i in interm :
            print("Ag" , int(i) , self.knowledge[int(i)-1])
        print(self.action)
        return ""

    def not_in(self,ens) :
        for elem in ens : 
            if getattr(elem, 'state') == self.state and getattr(elem, 'knowledge') == self.knowledge and getattr(elem, 'coalition') == self.coalition and getattr(elem, 'action') == self.action:
                return False 
        return True



class p_knowledge:
    def __init__(self, state, knowledge, agents):
        self.state = state
        self.knowledge = knowledge
        self.agents = agents
        
    def print_p_knowledge(self):
        print(self.state, self.knowledge, self.agents)
    
     # returns true if self is not in ens
    def not_in(self, ens) :
        for elem in ens :
            if getattr(elem, 'state') == self.state and getattr(elem, 'knowledge') == self.knowledge :
                return False 
        return True  
    
    def __eq__(self, other):
        if isinstance(other, p_knowledge):
            return self.state == other.state and self.knowledge == other.knowledge and self.agents == other.agents
        return False

    def __hash__(self):
        return hash((self.state, self.knowledge, self.agents))


class Node_PK:
   def __init__(self, data):
      self.left = None
      self.right = None
      self.value = data
