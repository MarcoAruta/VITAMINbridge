from vitamin_model_checker.logics.CTL.parser import *
import re

def natatl_to_ctl(natatl_formula): #transform a NatATL formula into a CTL formula (using "FORALL" path quantifier)
    k_pattern = r'(!?|not)?<\{((?:\d+,)*\d+)\},\s*(\d+)>'
    match = re.search(k_pattern, natatl_formula)
    negation = match.group(1)
    k_value = int(match.group(3))

    ctl_operator = "A"
    ctl_formula = re.sub(k_pattern, ctl_operator, natatl_formula)
    if negation:
        ctl_formula = f"!({ctl_formula})"

    return ctl_formula

def natatl_to_ctl_tree(node):
    pattern = r"<\{((?:\d+,)*\d+)\},\s*(\d+)>"
    if re.search(pattern, node.data):
        node.data = re.sub(pattern, "A", node.data)
    if node.left:
        natatl_to_ctl_tree(node.left)
    if node.right:
        natatl_to_ctl_tree(node.right)


#def get_agents_from_natatl(natatl_formula):
    # Extract k value from NatATL formula
 #   k_pattern = r'(!?|not)?<\{((?:\d+,)*\d+)\},\s*(\d+)>'
  #  match = re.search(k_pattern, natatl_formula)
    # Extract coalition from NatATL formula
   # agents_str = match.group(2)

    # Extract agents from coalition
    #agents = [int(agent) for agent in agents_str.split(',')]

    #return agents


def get_agents_from_natatl(natatl_formula):
    # Extract k value from NatATL formula
    k_pattern = r'(!?|not)?<\{((?:\d+,)*\d+)\},\s*(\d+)>'
    matches = re.findall(k_pattern, natatl_formula)

    # Extract agents from all matches
    agents = set()
    for match in matches:
        agents_str = match[1]
        agents.update(int(agent) for agent in agents_str.split(','))

    return list(agents)

#This function checks if a formula is complex or simple
def negated_formula(input):
    res = do_parsingCTL(input)
    #operators = ["!", "not", "and", "&&", "or", "||", "iff", "implies"]
    operators = ["!", "not"]
    if isinstance(res, tuple):
        return res[0] in operators
    return False

def get_k_value(natatl_formula):
    k_pattern = r'(!?|not)?<\{((?:\d+,)*\d+)\},\s*(\d+)>'
    match = re.search(k_pattern, natatl_formula)
    negation = match.group(1)
    k_value = int(match.group(3))

    return k_value

def replace_formula(formulaCTL, propositions_file):

    # Read the propositions.txt file
    with open(propositions_file, 'r') as file:
        propositions = file.read().split()

    # Replace the CTL formulas with atomic propositions
    temporal_operators = ["AX", "AF"]
    for operator in temporal_operators:
        # Create a pattern that matches the operator followed by any number of alphanumeric characters
        pattern = operator + r'\w*'
        # Find all matches in the formula
        matches = re.findall(pattern, formulaCTL)
        for match in matches:
            # Check if there are still propositions to replace with
            if propositions:
                # Replace the match with the first proposition and remove it from the list
                formulaCTL = formulaCTL.replace(match, propositions.pop(0), 1)
            else:
                print('Not enough propositions to replace all CTL formulas')
                return formulaCTL

    return formulaCTL

