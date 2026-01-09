import ply.lex as lex
import ply.yacc as yacc

# Tokens per formule LTL
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
    'PROP'
)

# Espressioni regolari per i token
t_LPAREN      = r'\('
t_RPAREN      = r'\)'
t_AND         = r'&&|\&|and'
t_OR          = r'\|\||\||or'
t_NOT         = r'!|not'
t_IMPLIES     = r'->|>|implies'
t_PROP        = r'[a-z]+'          # proposizioni atomiche
t_UNTIL       = r'U|until'
t_GLOBALLY    = r'G|globally|always'
t_NEXT        = r'X|next'
t_EVENTUALLY  = r'F|eventually'

# Gestione degli errori lessicali
def t_error(t):
    print(f"Carattere non valido: {t.value[0]}")
    t.lexer.skip(1)

# Regole grammaticali

# Regola per operatori binari: AND, OR, IMPLIES
def p_expression_binary(p):
    '''expression : expression AND expression
                  | expression OR expression
                  | expression IMPLIES expression'''
    p[0] = (p[2], p[1], p[3])

# Regola per l'operatore Until (binario)
def p_expression_until(p):
    'expression : expression UNTIL expression'
    p[0] = ('U', p[1], p[3])

# Regola per operatori temporali unari: NEXT, GLOBALLY, EVENTUALLY
def p_expression_unary_temporal(p):
    '''expression : NEXT expression
                  | GLOBALLY expression
                  | EVENTUALLY expression'''
    p[0] = (p[1], p[2])

# Regola per la negazione
def p_expression_not(p):
    'expression : NOT expression'
    p[0] = (p[1], p[2])

# Regola per le espressioni tra parentesi
def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

# Regola per le proposizioni atomiche
def p_expression_prop(p):
    'expression : PROP'
    p[0] = p[1]

def p_error(p):
    if p:
        print("Errore di sintassi in prossimità di", p.value)
    else:
        print("Errore di sintassi alla fine dell'input")

# Creazione del lexer e del parser
lexer = lex.lex()
parser = yacc.yacc()

def get_lexer():
    return lexer

# Data una formula LTL in input, restituisce una tupla che rappresenta la formula divisa in sottformule.
def do_parsingLTL(formula):
    try:
        result = parser.parse(formula)
        print("Risultato del parsing:", result)
        return result
    except SyntaxError:
        return None

# Funzione per verificare se un operatore specificato è presente nell'input
def verifyLTL(token_name, string):
    lexer.input(string)
    for token in lexer:
        if token.type == token_name and token.value in string:
            return True
    return False

# Esempio d'uso
if __name__ == "__main__":
    # Esempi di formule LTL
    formule = [
        "G(p->Fq)",
        "Xp",
        "pUq",
        "!(Fr)"
    ]

    for formula in formule:
        print(f"Parsing della formula: {formula}")
        risultato = do_parsingLTL(formula)
        print("Risultato:", risultato)
        print("-" * 40)

