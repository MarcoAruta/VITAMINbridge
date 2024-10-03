import re
import ply.lex as lex
import ply.yacc as yacc

# Token
tokens = (
    'LPAREN',
    'RPAREN',
    'AND',
    'OR',
    'NOT',
    'IMPLIES',
    'UNTIL',
    'RELEASE',
    'WEAK',
    'GLOBALLY',
    'NEXT',
    'EVENTUALLY',
    'FALSE',
    'TRUE',
    'PROP',
    'DEMONIC'
)

# Regular expressions for tokens
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_AND = r'&&|\&|and'
t_OR = r'\|\||\||or'
t_NOT = r'!|not'
t_IMPLIES = r'->|>|implies'
t_UNTIL = r'U|until'
t_RELEASE = r'R|release'
t_WEAK = r'W|weak'
t_GLOBALLY = r'G|globally|always'
t_NEXT = r'X|next'
t_EVENTUALLY = r'F|eventually'
t_FALSE = r'\#|false'
t_TRUE = r'\@|true'
t_PROP = r'[a-z]+'
t_DEMONIC = r'<J[1-9]\d*>'

# Token error handling
def t_error(t):
    t.lexer.skip(1)
    
class DemonicValueError(Exception):
    pass
    
# Grammar
def p_expression_binary(p):
    '''expression : expression AND expression
                  | expression OR expression
                  | expression IMPLIES expression'''
    p[0] = (p[2], p[1], p[3])

def p_expression_ternary(p):
    '''expression : DEMONIC expression UNTIL expression
                  | DEMONIC expression WEAK expression
                  | DEMONIC expression RELEASE expression'''
    demonic_cost = re.findall(r'\d+', p[1])[0]
    try:
        int(demonic_cost)
    except ValueError:
        raise DemonicValueError("Provided cost ({demonic_cost}) is not an int.")
    p[0] = (p[1] + p[3], p[2], p[4])


def p_expression_unary(p):
    '''expression : DEMONIC GLOBALLY expression
                  | DEMONIC NEXT expression
                  | DEMONIC EVENTUALLY expression'''
    demonic_cost = re.findall(r'\d+', p[1])[0]
    try:
        int(demonic_cost)
    except ValueError:
        raise DemonicValueError("Provided cost ({demonic_cost}) is not an int.")
    p[0] = (p[1] + p[2], p[3])


def p_expression_not(p):
    '''expression : NOT expression'''
    p[0] = (p[1], p[2])


def p_expression_group(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_expression_boolean(p):
    '''expression : FALSE 
                  | TRUE'''
    p[0] = p[1]


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


# given an ATL formula as input
# returns a tuple representing the formula divided into subformulas.
def do_parsing(formula):
    try:
        result = parser.parse(formula)
        return result
    except SyntaxError as e:  # if parser fails
        return None
    except DemonicValueError: # invalid cost
        return None


# checks whether the input operator corresponds to a given operator defined in the grammar
def verify(token_name, string):
    lexer.input(string)
    for token in lexer:
        if token.type == token_name and token.value in string:
            return True
    return False
