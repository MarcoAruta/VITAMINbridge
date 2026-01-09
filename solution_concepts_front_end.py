import streamlit as st


def validate_condition(cond, k, atomic_props):
    """
    Valida la condizione controllando che la sua complessità non superi il bound 'k'
    e che tutti i token (esclusi gli operatori logici) siano presenti nelle atomic propositions.

    Parameters:
      cond (str): La condizione da validare.
      k (int): Il bound massimo accettabile per la complessità della condizione.
      atomic_props (list): La lista delle atomic propositions valide.

    Returns:
      (bool, str): Una tupla contenente un valore booleano che indica se la condizione è valida e,
                   in caso contrario, un messaggio d'errore.
    """
    tokens = cond.split()
    # Calcola la complessità: numero di token + 1 se contiene "!"
    complexity = len(tokens) + (1 if "!" in cond else 0)
    if complexity > k:
        return False, f"La complessità della condizione ({complexity}) supera il bound k={k}."
    for token in tokens:
        # Ignora gli operatori logici comuni (case insensitive)
        if token.lower() in ["and", "or"]:
            continue
        # Se il token inizia con "!", controlla il simbolo dopo
        token_core = token[1:] if token.startswith("!") else token
        if token_core not in atomic_props:
            return False, f"Il simbolo '{token_core}' non è una atomic proposition valida."
    return True, ""


def display_solution_concepts(selected_agents, k, atomic_propositions):
    """
    Visualizza l'interfaccia per le 'SolutionConcepts' e restituisce le strategie elaborate (se presenti).

    Parameters:
      selected_agents (list): Lista degli agenti selezionati.
      k (int): Bound di complessità.
      atomic_propositions (list): Lista delle atomic propositions disponibili.

    Returns:
      dict or None: Un dizionario contenente le strategie per ciascun agente, se inserite correttamente.
    """
    solution_concept = st.selectbox('Select your Solution Concept', ['Is Not Nash', 'Sure Win', 'Exists Nash'])

    if solution_concept == 'Is Not Nash':
        st.info("Per ciascun agente, inserisci coppie condizione,azione (una per riga, formato: condizione,azione)")
        natural_strategies = {}
        with st.form(key="strategies_form"):
            # Creiamo un'area di input per ogni agente
            for agent in selected_agents:
                st.markdown(f"#### Agente {agent}")
                input_str = st.text_area(f"Inserisci le coppie condizione,azione per l'agente {agent}:",
                                         key=f"nat_{agent}")
                natural_strategies[agent] = input_str
            submitted = st.form_submit_button(label="Salva Strategie Naturali")

        if submitted:
            parsed_strategies = {}
            error_found = False
            # Elaborazione delle strategie inserite per ciascun agente
            for agent, input_str in natural_strategies.items():
                pairs = []
                for line in input_str.split("\n"):
                    line = line.strip()
                    if line:
                        parts = line.split(",")
                        if len(parts) != 2:
                            st.error(f"Formato non valido per l'agente {agent}: '{line}'. Uso: condizione,azione")
                            error_found = True
                        else:
                            cond = parts[0].strip()
                            act = parts[1].strip()
                            # Valida la condizione usando la funzione locale validate_condition
                            valid, err_msg = validate_condition(cond, k, atomic_propositions)
                            if not valid:
                                st.error(f"Errore per l'agente {agent} nella condizione '{cond}': {err_msg}")
                                error_found = True
                            else:
                                pairs.append((cond, act))
                parsed_strategies[agent] = {"condition_action_pairs": pairs}
            if not error_found:
                st.success("Strategie naturali inserite correttamente:")
                st.write(parsed_strategies)
            return parsed_strategies
    else:
        st.info("Funzionalità non implementata per questa opzione.")
        return None
