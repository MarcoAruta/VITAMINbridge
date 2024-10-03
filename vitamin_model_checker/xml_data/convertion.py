import xml.etree.ElementTree as ET

#The transition in mulval are calculated from teh end to the beginning, we then sweep the src and dst of each transition
class Transition:
    def __init__(self, src, dst):
        self.src = dst
        self.dst = src

# A node has an id, a fact (the knowledge or attack step it represent) and a type (if it's an attack or not). It may have a metric              
class Node: 
    def __init__(self, id, fact, metric, type):
        self.id = id
        self.fact = fact
        self.metric = metric
        self.type = type
        
#from the xml file we get the list of nodes and of transitions  
def build_data(file):
    tree = ET.parse(file)
    root = tree.getroot()
    transition = []
    vertices = []

    #we get the transitions
    for arc in root[0].findall('arc'):
        src = int(arc.find('src').text)
        dst = int(arc.find('dst').text)
        transition.append(Transition(src, dst))
    
    #we get the nodes
    for vertex in root[1].findall('vertex'):
        id = int(vertex.find('id').text) - 1
        fact = vertex.find('fact').text
        metric = int(vertex.find('metric').text)
        type = vertex.find('type').text
        vertices.append(Node(id, fact, metric, type))
        
    return (transition, vertices)


