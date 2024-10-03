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
t_PROP = r'[a-z\d_]+'
t_UNTIL = r'U|until'
t_GLOBALLY = r'G|globally|always'
t_NEXT = r'X|next'
t_EVENTUALLY = r'F|eventually'
t_COALITION = r'<\d+(?:,\d+)*>'


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
    coalition_values = re.findall(r'\d+', p[1])
    for value in coalition_values:
        if int(value) > int(MAX_COALITION):
            raise CoalitionValueError(f"Coalition value {value} exceeds maximum of {MAX_COALITION}")
    p[0] = (p[1] + p[3], p[2], p[4])


def p_expression_unary(p):
    '''expression : COALITION GLOBALLY expression
                  | COALITION NEXT expression
                  | COALITION EVENTUALLY expression'''
    coalition_values = re.findall(r'\d+', p[1])
    for value in coalition_values:
        if int(value) > int(MAX_COALITION):
            raise CoalitionValueError(f"Coalition value {value} exceeds maximum of {MAX_COALITION}")
    p[0] = (p[1] + p[2], p[3])


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


# given an ATL formula as input and the max number of agents in the model,
# returns a tuple representing the formula divided into subformulas.
def do_parsing(formula, n_agent):
    global MAX_COALITION
    MAX_COALITION = n_agent
    try:
        result = parser.parse(formula)
        # print(result)
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
