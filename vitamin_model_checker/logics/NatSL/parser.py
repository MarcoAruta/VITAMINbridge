import ply.lex as lex
import ply.yacc as yacc

# Tokens for NatSL
tokens = (
    'COLON',      # ':'
    'LPAREN',     # '('
    'RPAREN',     # ')'
    'COMMA',      # ','
    'EXIST',      # 'E'
    'FORALL',     # 'A'
    'BINDING',    # Variables per binding, ad es. 'x', 'y', 'z'
    'AGENT',      # Agenti (numeri, es. '1', '2', '3')
    'EVENTUALLY', # 'F'
    'PROP',       # Proposizioni, es. 'a', 'b', 'c'
    'NEG',        # Negazione '!'
    'BOUND'       # Espressione per il bound, es. "{3}"
)

# Regular expressions for tokens
t_COLON = r':'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COMMA = r','
t_EXIST = r'E'
t_FORALL = r'A'
t_BINDING = r'[xyz]'
t_AGENT = r'\d+'
t_EVENTUALLY = r'F'
t_PROP = r'[abcdefgh]'
t_NEG = r'!'
t_BOUND = r'\{\d+\}'

# Token error handling
def t_error(t):
    t.lexer.skip(1)

# Grammar rules for NatSL

def p_formula(p):
    '''formula : quantifiers COLON binding_pairs temporal_expression'''
    p[0] = (p[1], p[3], p[4])

def p_quantifiers(p):
    '''quantifiers : quantifier
                   | quantifiers quantifier'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

# Regola modificata per il quantificatore con bound opzionale.
def p_quantifier(p):
    '''quantifier : EXIST opt_bound BINDING
                  | FORALL opt_bound BINDING'''
    # p[1]: 'E' o 'A'
    # p[2]: il bound (intero) oppure default 1
    # p[3]: variabile binding
    p[0] = (p[1], p[3], p[2])

# Regola per il bound opzionale: se il token BOUND è presente, estrai il numero; altrimenti usa 1.
def p_opt_bound(p):
    '''opt_bound : BOUND
                 | empty'''
    if len(p) == 2 and p[1] is not None:
        # p[1] è una stringa del tipo "{3}"
        p[0] = int(p[1][1:-1])
    else:
        p[0] = 1

def p_empty(p):
    'empty :'
    p[0] = None

def p_binding_pairs(p):
    '''binding_pairs : binding_pair
                     | binding_pairs binding_pair'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_binding_pair(p):
    '''binding_pair : LPAREN BINDING COMMA AGENT RPAREN'''
    p[0] = (p[2], p[4])

def p_temporal_expression(p):
    '''temporal_expression : negation_expression
                           | EVENTUALLY PROP'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('F', p[2])

def p_negation_expression(p):
    '''negation_expression : NEG EVENTUALLY PROP'''
    p[0] = ('!', 'F', p[3])

# Error rule for syntax errors
def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}'")
    else:
        print("Syntax error at EOF")

# Build the lexer and parser
def get_lexer():
    return lex.lex()

def get_parser():
    return yacc.yacc()

def do_parsingNatSL(formula):
    lexer = get_lexer()
    parser = get_parser()
    try:
        result = parser.parse(formula, lexer=lexer)
        return result
    except SyntaxError:
        return None

def validate_bindings(parsed_formula):
    """
    Verifica che tutte le variabili dei quantificatori siano associate ad un agente.
    """
    quantifiers, binding_pairs, _ = parsed_formula
    bound_variables = {var for var, _ in binding_pairs}
    for _, binding_var, _ in quantifiers:
        if binding_var not in bound_variables:
            raise ValueError(f"Error: Binding variable '{binding_var}' non associata ad alcun agente.")

def count_agents(parsed_formula):
    """
    Conta il numero di agenti unici presenti nella formula.
    """
    _, binding_pairs, _ = parsed_formula
    agents = {int(agent) for _, agent in binding_pairs}
    return len(agents)

def extract_existential_agents(parsed_formula):
    """
    Estrae gli agenti esistenziali dalla formula NatSL.
    """
    quantifiers, binding_pairs, _ = parsed_formula
    existential_variables = [var for q, var, _ in quantifiers if q == 'E']
    map_vars_to_agents = {var: agent for var, agent in binding_pairs}
    return [int(map_vars_to_agents[var]) for var in existential_variables if var in map_vars_to_agents]

def extract_universal_agents(parsed_formula):
    """
    Estrae gli agenti universali dalla formula NatSL.
    """
    quantifiers, binding_pairs, _ = parsed_formula
    universal_variables = [var for q, var, _ in quantifiers if q == 'A']
    map_vars_to_agents = {var: agent for var, agent in binding_pairs}
    return [int(map_vars_to_agents[var]) for var in universal_variables if var in map_vars_to_agents]


def count_universal_agents(universal_agents):
    """
    Counts the number of universal agents
    """
    return len(universal_agents)

def count_existential_agents(existential_agents):
    """
    Counts the number of universal agents
    """
    return len(existential_agents)

def extract_formula(parsed_formula):
    """
    Estrae l'operatore temporale e la proposizione dalla formula NatSL.
    """
    _, _, temporal_expr = parsed_formula
    operator, proposition = temporal_expr
    return operator + proposition

def convert_natsl_to_ctl(parsed_formula, flag):
    """
    Converte una formula NatSL parsata nella corrispondente formula CTL usando il quantificatore universale 'A'.
    """
    quantifiers, binding_pairs, temporal_expr = parsed_formula

    if flag == 1:
        temporal_operator, proposition = temporal_expr
        ctl_formula = f"!A{temporal_operator}{proposition}"
    else:
        temporal_operator, proposition = temporal_expr
        ctl_formula = f"A{temporal_operator}{proposition}"

    return ctl_formula

def normalize_formula(formula):
    fully_negated = False

    if formula.startswith("!(") and formula.endswith(")"):
        fully_negated = True
        formula = formula[2:-1]

    quantifiers_part, rest = formula.split(":", 1)

    normalized_quantifiers = []
    for q in quantifiers_part:
        if q == 'E':
            normalized_quantifiers.append('A' if fully_negated else 'E')
        elif q == 'A':
            normalized_quantifiers.append('E' if fully_negated else 'A')
        else:
            normalized_quantifiers.append(q)

    normalized_formula = "".join(normalized_quantifiers) + ":" + rest
    return fully_negated, normalized_formula

def skolemize_formula(parsed_formula):
    """
    Applica la skolemizzazione, riscrivendo la formula con i quantificatori esistenziali prima e poi quelli universali.
    """
    quantifiers, binding_pairs, temporal_expr = parsed_formula

    existentials = [(q, var, bound) for q, var, bound in quantifiers if q == 'E']
    universals = [(q, var, bound) for q, var, bound in quantifiers if q == 'A']

    skolemized_quantifiers = existentials + universals
    return (skolemized_quantifiers, binding_pairs, temporal_expr)

def convert_natsl_to_natatl(natsl_formula):
    """
    Converte una formula NatSL in una o più formule NatATL.
    Ritorna una lista di formule NatATL.
    """
    parsed_formula = do_parsingNatSL(natsl_formula)
    if not parsed_formula:
        raise ValueError("Errore nel parsing della formula NatSL.")

    quantifiers, binding_pairs, temporal_expr = parsed_formula
    temporal_operator, proposition = temporal_expr
    natatl_formulas = []

    # Separazione di esistenziali e universali
    existential_vars = [(q, var, bound) for q, var, bound in quantifiers if q == 'E']
    universal_vars = [(q, var, bound) for q, var, bound in quantifiers if q == 'A']

    var_to_agent = {var: int(agent) for var, agent in binding_pairs}

    if existential_vars:
        existential_coalition = [var_to_agent[var] for _, var, _ in existential_vars if var in var_to_agent]
        total_bound = sum(bound for _, var, bound in existential_vars)
        coalition_str = "{" + ",".join(map(str, existential_coalition)) + "}"
        natatl_formulas.append(f"<{coalition_str}, {total_bound}>{temporal_operator}{proposition}")

    for _, var, bound in universal_vars:
        if var in var_to_agent:
            agent = var_to_agent[var]
            natatl_formulas.append(f"<{{{agent}}}, {bound}>{temporal_operator}{proposition}")
        else:
            raise ValueError(f"Variabile universale '{var}' non associata ad alcun agente.")

    if natsl_formula.startswith("!"):
        natatl_formulas = [f"!{formula}" for formula in natatl_formulas]

    return natatl_formulas

def convert_natsl_to_natatl_separated(natsl_formula):
    """
    Converte una formula NatSL nelle corrispondenti formule NatATL,
    separandole in esistenziali e universali.
    Ritorna una tupla: (formule_esistenziali, formule_universali)
    """
    parsed_formula = do_parsingNatSL(natsl_formula)
    if not parsed_formula:
        raise ValueError("Errore nel parsing della formula NatSL.")

    quantifiers, binding_pairs, temporal_expr = parsed_formula
    temporal_operator, proposition = temporal_expr

    existential_formulas = []
    universal_formulas = []

    var_to_agent = {var: int(agent) for var, agent in binding_pairs}

    existential_vars = [(q, var, bound) for q, var, bound in quantifiers if q == 'E']
    universal_vars = [(q, var, bound) for q, var, bound in quantifiers if q == 'A']

    if existential_vars:
        existential_coalition = [var_to_agent[var] for _, var, _ in existential_vars if var in var_to_agent]
        total_bound = sum(bound for _, var, bound in existential_vars)
        coalition_str = "{" + ",".join(map(str, existential_coalition)) + "}"
        existential_formulas.append(f"<{coalition_str}, {total_bound}>{temporal_operator}{proposition}")

    for _, var, bound in universal_vars:
        if var in var_to_agent:
            agent = var_to_agent[var]
            universal_formulas.append(f"<{{{agent}}}, {bound}>{temporal_operator}{proposition}")
        else:
            raise ValueError(f"Variabile universale '{var}' non associata ad alcun agente.")

    if natsl_formula.startswith("!"):
        existential_formulas = [f"!{formula}" for formula in existential_formulas]
        universal_formulas = [f"!{formula}" for formula in universal_formulas]

    return existential_formulas, universal_formulas

# Esempio d'uso
if __name__ == "__main__":
    # Esempio 1
    formula1 = "E{3}xA{4}y:(x,1)(y,2)Fa"
    print("Formula:", formula1)
    existential_natatl, universal_natatl = convert_natsl_to_natatl_separated(formula1)
    if existential_natatl:
        print("Formule NatATL esistenziali generate:", existential_natatl[0])
    else:
        print("Nessuna formula NatATL esistenziale generata.")
    if universal_natatl:
        print("Formule NatATL universali generate:", universal_natatl[0])
    else:
        print("Nessuna formula NatATL universale generata.")

    # Esempio 2
    formula2 = "E{3}xE{4}yA{2}z:(x,1)(y,2)(z,3)Fa"
    print("\nFormula:", formula2)
    existential_natatl, universal_natatl = convert_natsl_to_natatl_separated(formula2)
    if existential_natatl:
        print("Formule NatATL esistenziali generate:", existential_natatl[0])
    else:
        print("Nessuna formula NatATL esistenziale generata.")
    if universal_natatl:
        print("Formule NatATL universali generate:", universal_natatl[0])
    else:
        print("Nessuna formula NatATL universale generata.")

    # Esempio con formula SENZA bound esplicito (usa default bound 1)
    formula = "ExAy:(x,1)(y,2)Fa"
    print("Formula:", formula)

    # Convert NatSL to NatATL
    converted_formulas = convert_natsl_to_natatl(formula)
    print("Formule NatATL generate:", converted_formulas)

    # Separate NatATL formulas into existential and universal
    existential_natatl, universal_natatl = convert_natsl_to_natatl_separated(formula)

    if existential_natatl:
        print("Formule NatATL esistenziali generate:", existential_natatl[0])
    else:
        print("Nessuna formula NatATL esistenziale generata.")

    if universal_natatl:
        print("Formule NatATL universali generate:", universal_natatl[0])
    else:
        print("Nessuna formula NatATL universale generata.")

    # Normalize the formula
    flag, normalized_formula = normalize_formula(formula)
    print("Formula Normalizzata:", normalized_formula)
    flag, normalized_formula1 = normalize_formula(formula1)
    print("Formula1 Normalizzata:", normalized_formula1)
    flag, normalized_formula2 = normalize_formula(formula2)
    print("Formula1 Normalizzata:", normalized_formula2)

    # Parse the normalized formula
    parsed = do_parsingNatSL(normalized_formula)
    parsed1 = do_parsingNatSL(normalized_formula1)
    parsed2 = do_parsingNatSL(normalized_formula2)
    if parsed:
        try:
            validate_bindings(parsed)
            print("Formula Parsata:", parsed)
            validate_bindings(parsed1)
            print("Formula1 Parsata:", parsed)
            validate_bindings(parsed2)
            print("Formula2 Parsata:", parsed)

            skolemized = skolemize_formula(parsed)
            print("Formula Skolemizzata:", skolemized)
            skolemized1 = skolemize_formula(parsed1)
            print("Formula1 Skolemizzata:", skolemized1)
            skolemized2 = skolemize_formula(parsed2)
            print("Formula2 Skolemizzata:", skolemized2)

            agent_count = count_agents(parsed)
            print("Numero di Agenti:", agent_count)

            existential_agents = extract_existential_agents(parsed)
            print("Agenti Esistenziali:", existential_agents)

            universal_agents = extract_universal_agents(parsed)
            print("Agenti Universali:", universal_agents)

            n_universal = count_universal_agents(universal_agents)
            print("Numero di Agenti Universali", n_universal)

            temporal_operator_and_prop = extract_formula(parsed)
            print("Operatore Temporale e Proposizione:", temporal_operator_and_prop)

            ctl_formula = convert_natsl_to_ctl(parsed, flag)
            print("CTL Formula:", ctl_formula)

        except ValueError as e:
            print(e)
    else:
        print("Errore nel parsing della formula.")
