from vitamin_model_checker.logics.CTL.parser import *
import re

def natatl_to_ctl(natatl_formula: str):
    """
    Transform a NatATL formula into a CTL formula (using universal path quantifier A).

    Supports coalition agents as:
      - numbers: <{1,2}, 3> ...
      - names:   <{robot_arm, conveyor}, 3> ...
    Supports optional negation prefix: !<{...},k>...  or not<{...},k>...
    """
    if natatl_formula is None:
        raise ValueError("natatl_formula is None")

    natatl_formula = str(natatl_formula).strip()

    # group(1) = optional negation prefix (! or not)
    # group(2) = coalition content (anything except '}'), e.g., "1,2" or "robot_arm, conveyor"
    # group(3) = k as digits
    k_pattern = r'(?:(!|not)\s*)?<\s*\{\s*([^}]*)\s*\}\s*,\s*(\d+)\s*>'

    match = re.search(k_pattern, natatl_formula)
    if not match:
        raise ValueError(
            f"Invalid NatATL coalition/k prefix. Expected something like <{{a,b}}, k> ... "
            f"Got: {natatl_formula}"
        )

    negation = match.group(1)   # '!' or 'not' or None
    # coalition_raw = match.group(2)  # not used here, but kept if you need it
    # k_value = int(match.group(3))   # not used here, but kept if you need it

    ctl_formula = re.sub(k_pattern, "A", natatl_formula, count=1)

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


def get_agents_from_natatl(natatl_formula: str, model_agents: list[str] | None = None):
    """
    Returns coalition agents as 1-based indices (to match existing code).
    - If coalition contains numbers: uses them directly.
    - If coalition contains names: requires model_agents list to map name -> index.

    Example:
      model_agents = ["robot_arm","conveyor"]
      <{robot_arm}, 2> ... -> [1]
      <{conveyor, robot_arm}, 2> ... -> [2,1]
      <{1,2}, 2> ... -> [1,2]
    """
    if natatl_formula is None:
        raise ValueError("NatATL formula is None")

    natatl_formula = str(natatl_formula).strip()

    m = re.search(r'<\s*\{\s*([^}]*)\s*\}\s*,', natatl_formula)
    if not m:
        raise ValueError(f"Invalid NatATL formula: cannot extract coalition. Got: {natatl_formula}")

    inside = m.group(1).strip()
    if not inside:
        return []

    items = [x.strip() for x in inside.split(",") if x.strip()]

    # If all numeric -> return them as ints
    if all(re.fullmatch(r"\d+", it) for it in items):
        return [int(it) for it in items]

    # Otherwise they are names -> need model_agents
    if not model_agents:
        raise ValueError(
            f"Coalition uses agent names ({items}) but model_agents was not provided for mapping."
        )

    name_to_idx = {name: i + 1 for i, name in enumerate(model_agents)}

    out = []
    for name in items:
        if name not in name_to_idx:
            raise ValueError(
                f"Agent '{name}' not found in model_agents={model_agents}. Cannot map coalition."
            )
        out.append(name_to_idx[name])

    return out



#This function checks if a formula is complex or simple
def negated_formula(input):
    res = do_parsingCTL(input)
    #operators = ["!", "not", "and", "&&", "or", "||", "iff", "implies"]
    operators = ["!", "not"]
    if isinstance(res, tuple):
        return res[0] in operators
    return False

def get_k_value(natatl_formula: str) -> int:
    """
    Extracts k from NatATL formula prefix.
    Supports both numeric and named coalitions:
      <{1,2}, 3> ...
      <{robot_arm, conveyor}, 3> ...
    """
    if natatl_formula is None:
        raise ValueError("NatATL formula is None")

    natatl_formula = str(natatl_formula).strip()

    # group(2) is k
    k_pattern = r'(?:(!|not)\s*)?<\s*\{\s*[^}]*\s*\}\s*,\s*(\d+)\s*>'
    match = re.search(k_pattern, natatl_formula)
    if not match:
        raise ValueError(f"Invalid NatATL formula: cannot extract k. Got: {natatl_formula}")

    return int(match.group(2))

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

