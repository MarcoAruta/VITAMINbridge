import ply.lex as lex
import ply.yacc as yacc
import re
from vitamin_model_checker.models.CGS import *
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Recall.strategies import cgs

# Tokens
tokens = (
    'LPAREN',
    'RPAREN',
    'AND',
    'OR',
    'NOT',
    'IMPLIES',
    'STAR',
    'CONCAT',
    'CHOICE',
    'PROP'
)

# Regular expressions for tokens
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_AND = r'&&|\&|and'
t_OR = r'\|\||\||or'
t_NOT = r'!|not'
t_IMPLIES = r'->|>|implies'
t_STAR = r'\*'
t_CONCAT = r'\.'
t_CHOICE = r'\|'
t_PROP = r'[a-z]+'

# Token error handling
def t_error(t):
    t.lexer.skip(1)

# Grammar
def p_expression_binary(p):
    '''expression : expression AND expression
                  | expression OR expression
                  | expression IMPLIES expression
                  | expression CONCAT expression
                  | expression CHOICE expression'''
    p[0] = (p[2], p[1], p[3])

def p_expression_unary(p):
    '''expression : NOT expression
                  | expression STAR'''
    p[0] = (p[1], p[2]) if len(p) == 3 else (p[1])

def p_expression_group(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_expression_prop(p):
    '''expression : PROP'''
    p[0] = p[1]

def p_error(p):
    pass

# lexer and parser
lexer = lex.lex()
parser = yacc.yacc()

def get_lexer():
    return lexer

# given a boolean formula as input, returns a tuple representing the formula divided into subformulas.
def do_parsing_boolean(formula):
    try:
        result = parser.parse(formula)
        print(result)
        return result
    except SyntaxError:  # if parser fails
        return None

# checks whether the input operator corresponds to a given operator defined in the grammar
def verify_boolean(token_name, string):
    lexer.input(string)
    for token in lexer:
        if token.type == token_name and token.value in string:
            return True
    return False

def is_regex_or_boolean_formula(pattern):
    regex_special_chars = r"[*+?.()|{}[\]]"

    # Controlla se contiene caratteri speciali delle regex
    if re.search(regex_special_chars, pattern):
        return "Regex"
    else:
        return "Boolean Formula"



def solve_regex_tree(node, transitions):

    if node.left is not None:
        print(f"node left: {node.left}")
        print(type(node.left))
        solve_regex_tree(node.left, transitions)

    if node.right is not None:
        print(f"node right: {node.right}")
        solve_regex_tree(node.right, transitions)

    if node.right is None:   # UNARY OPERATORS: not, globally, next, eventually
        if verify_boolean('NOT', node.value):  # e.g. ¬φ
            states = string_to_set(node.left.value)
            ris = set(cgs.get_states()) - states
            node.value = str(ris)

        # STAR operator
        elif verify_boolean('STAR', node.value):  # e.g. φ*
            states = string_to_set(node.left.value)
            proposition = node.left.true_props #INTEGRA CAMPO PROPS MANCANTE CHE INDICA LE PROPOSIZIONI VERE IN QUELLO STATO CORRENTE
            ris = compute_star(states, proposition, transitions)
            node.value = str(ris)

    if node.left is not None and node.right is not None:  # BINARY OPERATORS: or, and, until, implies
        if verify_boolean('OR', node.value): # e.g. φ || θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.union(states2)
            node.value = str(ris)

        elif verify_boolean('AND', node.value):  # e.g. φ && θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.intersection(states2)
            node.value = str(ris)

        elif verify_boolean('IMPLIES', node.value):  # e.g. φ -> θ
            # p -> q ≡ ¬p ∨ q
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            not_states1 = set(cgs.get_states()).difference(states1)
            ris = not_states1.union(states2)
            node.value = str(ris)

        # CONCATENATION operator
        elif verify_boolean('CONCAT', node.value):  # e.g. φ ; θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            proposition1 = node.left.true_props  #INTEGRA CAMPO PROPS MANCANTE CHE INDICA LE PROPOSIZIONI VERE IN QUELLO STATO CORRENTE
            proposition2 = node.right.true_props  #INTEGRA CAMPO PROPS MANCANTE CHE INDICA LE PROPOSIZIONI VERE IN QUELLO STATO CORRENTE
            ris = compute_concatenation(states1, states2, proposition1, proposition2, transitions)
            node.value = str(ris)


def compute_star(states, proposition, transitions):
    #Computes the set of states that satisfy the Kleene star operation with respect to a proposition.
    #This includes zero or more repetitions of the states where the proposition is true.

    reachable_states = set(states)
    current_states = set(states)

    while current_states:
        next_states = set()
        for state in current_states:
            for next_state in cgs.get_reachable_states(transitions, state):
                if next_state not in reachable_states and proposition in next_state.true_props:
                    next_states.add(next_state)
                    reachable_states.add(next_state)
        current_states = next_states
#lunghezza traccia in base alla natura dell'espressione regolare (es: p*q e la lunghezza della traccia è 3 p va verificato sui due stati e q sull'ultimo)
    return reachable_states


def compute_concatenation(states1, states2, proposition1, proposition2, transitions):
    #Computes the set of states that satisfy the concatenation of states1 and states2
    #with respect to propositions.

    reachable_states = set()

    for state1 in states1:
        if proposition1 in state1.true_props:
            next_states = cgs.get_reachable_states(transitions, state1)
            for state2 in next_states:
                if proposition2 in state2.true_props and state2 in states2:
                    reachable_states.add(state2)

    return reachable_states


def verify_boolean(op, value):
    #This function returns True if the value matches the operator op.
    return op.lower() in value.lower()


# converts a string into a set
def string_to_set(string):
    #print(f"string:{string}")
    if string == 'set()':
        return set()
    set_list = string.strip("{}").split(", ")
    new_string = "{" + ", ".join(set_list) + "}"
    return eval(new_string)

def check_prop_holds_in_label_row(prop, prop_matrix):
    def eval_prop(prop):
        if 'and' in prop:
            sub_props = prop.split('and')
            return all(eval_prop(sub_prop.strip()) for sub_prop in sub_props)
        elif 'or' in prop:
            sub_props = prop.split('or')
            return any(eval_prop(sub_prop.strip()) for sub_prop in sub_props)
        elif prop.startswith('!'):
            return not eval_prop(prop[1:].strip())
        else:
            index = cgs.get_atom_index(prop.strip())
            print(f"indice {index}")
            if index is None:
                return False
            source = prop_matrix[index]
            print(f"la prop index in essa equivale a {source}")
            print(f"presa la seguente label row {prop_matrix}")
            return source == 1

    result = eval_prop(prop)
    if result:
        print("ho ritornato true")
    return result