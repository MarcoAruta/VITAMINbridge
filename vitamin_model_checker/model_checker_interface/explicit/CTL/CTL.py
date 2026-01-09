from binarytree import Node
from vitamin_model_checker.logics.CTL import verifyCTL, do_parsingCTL
from vitamin_model_checker.models.CGS.CGS import *

# -------------------------------
# FUNZIONI DI SUPPORTO E UTILITÀ
# -------------------------------

def get_states_prop_holds(cgs, prop):
    """
    Restituisce l'insieme degli stati in cui la proposizione prop è vera.
    """
    states = set()
    prop_matrix = cgs.get_matrix_proposition()
    index = cgs.get_atom_index(prop)
    if index is None:
        return None
    for state, row in enumerate(prop_matrix):
        if row[int(index)] == 1:
            states.add(state)
    return states

def convert_state_set(cgs, state_set):
    """
    Converte un insieme di nomi di stati (es. {"s1", "s2"}) nel corrispondente insieme di indici.
    """
    states = set()
    for elem in state_set:
        position = cgs.get_index_by_state_name(elem)
        states.add(int(position))
    return states

def string_to_set(string):
    """
    Converte una stringa rappresentante un insieme (es. "{s1, s2}") in un oggetto set.
    """
    if string == 'set()':
        return set()
    set_list = string.strip("{}").split(", ")
    new_string = "{" + ", ".join(set_list) + "}"
    return eval(new_string)

def build_tree(cgs, tpl):
    """
    Costruisce ricorsivamente l'albero della formula (di tipo binary tree).
    Se il nodo è un atomo, si sostituisce il nodo con la stringa dell'insieme degli stati
    in cui l'atomo è vero.
    """
    if isinstance(tpl, tuple):
        root = Node(tpl[0])
        if len(tpl) > 1:
            left_child = build_tree(cgs, tpl[1])
            if left_child is None:
                return None
            root.left = left_child
            if len(tpl) > 2:
                right_child = build_tree(cgs, tpl[2])
                if right_child is None:
                    return None
                root.right = right_child
    else:
        # Nodo atomico: costruisce il set degli stati dove la proposizione è vera.
        states = set()
        states_proposition = get_states_prop_holds(cgs, str(tpl))
        if states_proposition is None:
            return None
        else:
            for element in states_proposition:
                # converti sempre in Python-str
                state_name = str(cgs.get_state_name_by_index(element))
                states.add(state_name)
            root = Node(str(states))
    return root

# ---------------------------------------------------------
# FUNZIONI PER IL CALCOLO DELLE PRE-IMMAGINI (CTL)
# ---------------------------------------------------------

def pre_image_exist(transitions, list_holds_p):
    """
    Calcola la pre-immagine esistenziale:
    Restituisce l'insieme degli stati s tali che esista una transizione (s,t)
    con t appartenente a list_holds_p.
    """
    pre_list = set()
    for state in list(list_holds_p):
        # Per ogni stato t in list_holds_p, si raccolgono tutti gli s tali che (s,t) è una transizione
        predecessors = {s for (s, t) in transitions if t == state}
        pre_list.update(predecessors)
    return pre_list

def pre_image_all(transitions, states_set, holds_p):
    """
    Calcola la pre-immagine universale (AX):
    Restituisce gli stati in states_set per i quali, se lo stato ha dei successori,
    tutti i successori appartengono a holds_p.
    (Per deadlock, si assume che AX sia vera.)
    """
    pre_states = set()
    for state in states_set:
        # Raccolgo i successori di 'state'
        successors = {t for (s, t) in transitions if s == state}
        if not successors or successors.issubset(holds_p):
            pre_states.add(state)
    return pre_states

def pre_release_A(cgs, holds_phi, holds_psi):
    """
    Calcola A(φ R ψ) attraverso il massimo fixpoint.
    Restituisce l'insieme dei stati in cui vale A(φ R ψ),
    cioè gli stati s tali che:
      - s soddisfa ψ, e
      - se s non soddisfa φ, allora ogni successore di s appartiene al fixpoint.
    """
    all_states = set(cgs.get_states())
    # Inizialmente, il risultato (fixpoint) è dato dagli stati che soddisfano ψ.
    result = holds_psi.copy()
    transitions = cgs.get_edges()
    while True:
        new_result = set()
        for s in all_states:
            if s in holds_psi:
                # Controllo: se s soddisfa φ oppure tutti i successori di s (se esistenti)
                # sono già in result, allora s entra in new_result.
                successors = {t for (s_, t) in transitions if s_ == s}
                if (s in holds_phi) or (not successors) or (successors.issubset(result)):
                    new_result.add(s)
        if new_result == result:
            break
        result = new_result
    return result

# ------------------------------
# FUNZIONE DI RISOLUZIONE DELL'ALBERO
# ------------------------------

def solve_tree(cgs, node):
    """
    Risolve ricorsivamente l'albero della formula in base all'operatore.
    La soluzione viene memorizzata in node.value, che contiene la stringa
    rappresentante l'insieme degli stati in cui la formula è vera.
    """
    # Risolvi i sottoalberi (ricorsione)
    if node.left is not None:
        solve_tree(cgs, node.left)
    if node.right is not None:
        solve_tree(cgs, node.right)

    # OPERATORE UNARIO
    if node.right is None:
        if verifyCTL('NOT', node.value):  # ¬φ
            states = string_to_set(node.left.value)
            ris = set(cgs.get_states()) - states
            node.value = str(ris)

        elif verifyCTL('EXIST', node.value) and verifyCTL('NEXT', node.value):  # EX φ
            states = string_to_set(node.left.value)
            ris = pre_image_exist(cgs.get_edges(), states)
            node.value = str(ris)

        elif verifyCTL('FORALL', node.value) and verifyCTL('NEXT', node.value):  # AX φ
            states = string_to_set(node.left.value)
            ris = pre_image_all(cgs.get_edges(), cgs.get_states(), states)
            node.value = str(ris)

        elif verifyCTL('EXIST', node.value) and verifyCTL('EVENTUALLY', node.value):  # EF φ
            # EF φ = least fixpoint: T = φ ∪ (EX φ) iterato
            target = string_to_set(node.left.value)
            T = target.copy()
            while True:
                new_T = T.union(pre_image_exist(cgs.get_edges(), T))
                if new_T == T:
                    break
                T = new_T
            node.value = str(T)


        elif verifyCTL('FORALL', node.value) and verifyCTL('EVENTUALLY', node.value):  # AF φ

            not_phi = set(cgs.get_states()) - string_to_set(node.left.value)

            # EG(not_phi): greatest fixpoint T = not_phi ∩ EX(T)

            T = set(cgs.get_states())

            while True:

                new_T = not_phi.intersection(pre_image_exist(cgs.get_edges(), T))

                if new_T == T:
                    break

                T = new_T

            node.value = str(set(cgs.get_states()) - T)


        elif verifyCTL('EXIST', node.value) and verifyCTL('GLOBALLY', node.value):  # EG φ
            # EG φ = greatest fixpoint: T = φ ∩ EX T
            target = string_to_set(node.left.value)
            T = set(cgs.get_states())
            while True:
                new_T = target.intersection(pre_image_exist(cgs.get_edges(), T))
                if new_T == T:
                    break
                T = new_T
            node.value = str(T)

        elif verifyCTL('FORALL', node.value) and verifyCTL('GLOBALLY', node.value):  # AG φ
            # AG φ = ¬EF(¬φ)
            target = set(cgs.get_states()) - string_to_set(node.left.value)
            T = target.copy()
            while True:
                new_T = T.union(pre_image_exist(cgs.get_edges(), T))
                if new_T == T:
                    break
                T = new_T
            node.value = str(set(cgs.get_states()) - T)

        # Operatore RELEASE (versione universale, AR)
        elif verifyCTL('FORALL', node.value) and verifyCTL('RELEASE', node.value):  # A(φ R ψ)
            # Supponiamo che l'albero binario: left -> φ, right -> ψ oppure viceversa
            # A(φ R ψ) richiede: ψ ∧ (φ ∨ AX (φ R ψ))
            # Utilizziamo la caratterizzazione tramite fixpoint:
            holds_phi = string_to_set(node.left.value)
            holds_psi = string_to_set(node.right.value)
            ris = pre_release_A(cgs, holds_phi, holds_psi)
            node.value = str(ris)

    # OPERATORE BINARIO
    if node.left is not None and node.right is not None:
        if verifyCTL('OR', node.value):  # φ ∨ θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.union(states2)
            node.value = str(ris)

        elif verifyCTL('AND', node.value):  # φ ∧ θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.intersection(states2)
            node.value = str(ris)

        elif verifyCTL('IMPLIES', node.value):  # φ -> θ  ≡ ¬φ ∨ θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            not_states1 = set(cgs.get_states()) - states1
            ris = not_states1.union(states2)
            node.value = str(ris)

        elif verifyCTL('EXIST', node.value) and verifyCTL('UNTIL', node.value):  # E(φ U ψ)
            # Calcolo del least fixpoint: T = ψ ∪ (φ ∩ EX T)
            states_phi = string_to_set(node.left.value)
            states_psi = string_to_set(node.right.value)
            T = states_psi.copy()
            while True:
                new_T = T.union(states_phi.intersection(pre_image_exist(cgs.get_edges(), T)))
                if new_T == T:
                    break
                T = new_T
            node.value = str(T)

        elif verifyCTL('FORALL', node.value) and verifyCTL('UNTIL', node.value):  # A(φ U ψ)
            # A(φ U ψ) = ¬E(¬ψ U (¬φ ∧ ¬ψ)) (formula duale)
            # Possiamo calcolarla tramite una trasformazione:
            not_states_phi = set(cgs.get_states()) - string_to_set(node.left.value)
            not_states_psi = set(cgs.get_states()) - string_to_set(node.right.value)
            # Calcoliamo E(not ψ U (not φ ∧ not ψ))
            T = not_states_psi.copy()
            while True:
                new_T = T.union((not_states_phi.intersection(not_states_psi)).intersection(pre_image_exist(cgs.get_edges(), T)))
                if new_T == T:
                    break
                T = new_T
            # Complemento: A(φ U ψ) = ¬T
            node.value = str(set(cgs.get_states()) - T)

        # Per l'operatore RELEASE esistenziale (se necessario) si potrebbe definire in maniera duale,
        # ad esempio: E(φ R ψ) = ¬A(¬φ U ¬ψ)
        elif verifyCTL('EXIST', node.value) and verifyCTL('RELEASE', node.value):  # E(φ R ψ)
            not_states_phi = set(cgs.get_states()) - string_to_set(node.left.value)
            not_states_psi = set(cgs.get_states()) - string_to_set(node.right.value)
            # Calcoliamo A(not φ U not ψ)
            T = not_states_psi.copy()
            while True:
                new_T = T.union(not_states_phi.intersection(not_states_psi).intersection(pre_image_all(cgs.get_edges(), cgs.get_states(), T)))
                if new_T == T:
                    break
                T = new_T
            node.value = str(set(cgs.get_states()) - T)

# -------------------------------------
# FUNZIONE DI MODEL CHECKING (CTL)
# -------------------------------------

def verify_initial_state(initial_state, result_str):
    """
    Verifica se lo stato iniziale è incluso nell'insieme risultante (espresso come stringa).
    """
    return str(initial_state) in result_str

def model_checking(cgs, formula, filename):
    """
    Esegue il model checking per CTL:
      1. Legge il modello dal file
      2. Parsea la formula
      3. Costruisce l'albero della formula
      4. Risolve l'albero
      5. Restituisce il risultato (insieme degli stati dove la formula è vera) e l'esito sullo stato iniziale
    """
    if not formula.strip():
        result = {'res': 'Error: formula non inserita', 'initial_state': ''}
        return result

    # Parsing del modello
    cgs.read_file(filename)
    # Parsing della formula CTL
    res_parsing = do_parsingCTL(formula)
    if res_parsing is None:
        result = {'res': "Errore di sintassi nella formula", 'initial_state': ''}
        return result
    root = build_tree(cgs, res_parsing)
    if root is None:
        result = {'res': "Errore di sintassi: l'atomo non esiste", 'initial_state': ''}
        return result

    # Esecuzione del model checking
    solve_tree(cgs, root)

    # Risultato: verifico se lo stato iniziale soddisfa la formula
    initial_state = cgs.get_initial_state()
    bool_res = verify_initial_state(initial_state, root.value)
    result = {'res': 'Result: ' + str(root.value),
              'initial_state': 'Initial state ' + str(initial_state) + ": " + str(bool_res)}
    return result

