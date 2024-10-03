import re
import ply.lex as lex
import ply.yacc as yacc

MAX_COALITION = 0

# Token
tokens = (
    'LPAREN',
    'RPAREN',
    'AND',
    'OR',
    'NOT',
    'IMPLIES',
    'UNTIL',
    'GLOBALLY',
    'NEXT',
    'EVENTUALLY',
    'PROP',
    'COALITION'
)


# Regular expressions for tokens
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_AND = r'&&|\&|and'
t_OR = r'\|\||\||or'
t_NOT = r'!|not'
t_IMPLIES = r'->|>|implies'
t_PROP = r'[a-z]+'
t_UNTIL = r'U|until'
t_GLOBALLY = r'G|globally|always'
t_NEXT = r'X|next'
t_EVENTUALLY = r'F|eventually'
t_COALITION = r'<\{((?:\d+,)*\d+)\},\s*(\d+)>'


# Token error handling
def t_error(t):
    t.lexer.skip(1)



# Grammar
def p_expression_binary(p):
    '''expression : expression AND expression
                  | expression OR expression
                  | expression IMPLIES expression'''
    p[0] = (p[2], p[1], p[3])


class CoalitionValueError(Exception):
    pass

def p_expression_ternary(p):
    '''expression : COALITION expression UNTIL expression'''
    matches = re.findall(r'\{((?:\d+,)*\d+)\},\s*(\d+)', p[1])
    if matches:
        coalition_values, k_value = matches[0]
        for value in coalition_values.split(','):
            if int(value) > int(MAX_COALITION):
                raise CoalitionValueError(f"Coalition value {value} exceeds maximum of {MAX_COALITION}")
        p[0] = (f"<{{{coalition_values}}}, {k_value}>{p[3]}", p[2], p[4])

def p_expression_unary(p):
    '''expression : COALITION GLOBALLY expression
                  | COALITION NEXT expression
                  | COALITION EVENTUALLY expression'''
    matches = re.findall(r'\{((?:\d+,)*\d+)\},\s*(\d+)', p[1])
    if matches:
        coalition_values, k_value = matches[0]
        for value in coalition_values.split(','):
            if int(value) > int(MAX_COALITION):
                raise CoalitionValueError(f"Coalition value {value} exceeds maximum of {MAX_COALITION}")
        p[0] = (f"<{{{coalition_values}}}, {k_value}>{p[2]}", p[3])


def p_expression_not(p):
    '''expression : NOT expression'''
    p[0] = (p[1], p[2])


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


# given a natATL formula as input and the max number of agents in the model,
# returns a tuple representing the formula divided into subformulas.
def do_parsing(formula, n_agent):
    global MAX_COALITION
    MAX_COALITION = n_agent
    try:
        result = parser.parse(formula)
        print(result)
        return result
    except SyntaxError:  # if parser fails
        return None
    except CoalitionValueError:  # coalition not existent
      return None


# checks whether the input operator corresponds to a given operator defined in the grammar
def verify(token_name, string):
    lexer.input(string)
    for token in lexer:
        if token.type == token_name and token.value in string:
            return True
    return False

#use example: "formula = "<{1,2}, 5> (a && b) U (c || !d)",
# scritta anche come "('<{1,2},5>U', ('&&', 'a', 'b'), ('||', 'c', ('!', 'd')))"