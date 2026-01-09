from vitamin_model_checker.model_checker_interface.explicit.CTL import model_checking
from vitamin_model_checker.models.CGS import CGS
import re
import ast

pruned_model_file = "./tmp.txt"


def normalize_ctl_condition(cond: str) -> str:
    if cond is None:
        return ""
    s = str(cond)
    s = s.replace("∧", "&").replace("∨", "|").replace("¬", "!").replace("→", ">")
    s = re.sub(r"\bnot\b", "!", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _parse_ctl_states(res: dict):
    """
    Estrae l'insieme di stati dalla stringa 'Result: {...}' ritornata da CTL.model_checking.
    Ritorna: set(...) oppure None se formato inatteso.
    """
    if not isinstance(res, dict) or "res" not in res:
        return None
    res_str = res.get("res", "")
    if ": " not in res_str:
        return None
    try:
        return ast.literal_eval(res_str.split(": ", 1)[1])
    except Exception:
        return None


def modify_matrix_hard(graph, label_matrix, states, action, agent_index, agents, state_to_idx):
    """
    HARD semantics: tiene SOLO le joint-actions dove l'agente agent_index fa ESATTAMENTE `action`.
    (Mai idle permissivo.)

    Ritorna: (new_graph, invalid_states)
      invalid_states = stati in `states` la cui riga diventa tutta 0 dopo il pruning.
    """
    new_graph = [row.copy() for row in graph]
    idx = agents[agent_index - 1] - 1  # posizione agente nella joint-action

    for i, row in enumerate(new_graph):
        for j, elem in enumerate(row):
            if label_matrix[i][j] in states:
                if isinstance(elem, str) and elem != "*":
                    kept = []
                    for part in elem.split(","):
                        part = part.strip()
                        if not part:
                            continue
                        if len(part) > idx and part[idx] == action:
                            kept.append(part)
                    new_graph[i][j] = ",".join(kept) if kept else 0

    invalid_states = set()
    for s in states:
        r = state_to_idx.get(s)
        if r is None:
            continue
        if all(x == 0 for x in new_graph[r]):
            invalid_states.add(s)

    return new_graph, invalid_states


def process_transition_matrix_data(cgs, model_path, agents, *strategies):
    """
    Applica il pruning per ogni agente della coalizione seguendo la strategia.
    HARD: nessun fallback a idle.

    Ritorna: (graph, reason)
      - graph è None se la strategia è non ammissibile (perché impone azioni non abilitate)
      - reason spiega perché
    """
    graph = cgs.get_graph()
    label_matrix = cgs.create_label_matrix(graph)
    all_states = set(cgs.get_states())
    state_to_idx = {s: i for i, s in enumerate(cgs.get_states())}

    print(f"initial transition matrix: {graph}")

    actions_per_agent = cgs.get_actions(agents)
    for agent_key, acts in actions_per_agent.items():
        print(f"actions_{agent_key}")
        print(acts)

    for strategy_index, strategy in enumerate(strategies, start=1):
        covered = set()

        for (condition, action) in strategy["condition_action_pairs"]:
            condition = str(condition).strip()
            action = str(action).strip()

            # --- caso T: default sugli stati rimanenti ---
            if condition.upper() == "T":
                target_states = all_states - covered
                if not target_states:
                    continue

                covered |= target_states
                graph, invalid = modify_matrix_hard(
                    graph, label_matrix, target_states, action, strategy_index, agents, state_to_idx
                )

                if invalid:
                    reason = (
                        f"Strategia NON ammissibile (HARD): regola (T -> {action}) "
                        f"svuota la riga in {sorted(invalid)}. "
                        f"Significa che '{action}' non è abilitata in quegli stati."
                    )
                    return None, reason

                print(f"[T] new transition matrix: {graph} modified by agent {strategy_index}")
                continue

            # --- CTL normale ---
            condition_norm = normalize_ctl_condition(condition)
            ctl_res = model_checking(cgs, condition_norm, model_path)
            print(f"[DBG] cond={condition_norm} -> {ctl_res}")

            state_set = _parse_ctl_states(ctl_res)
            if state_set is None:
                # formato inatteso -> non faccio danni, skip
                print(f"[WARN] CTL result unparsable for '{condition_norm}': {ctl_res}")
                continue

            if not state_set:
                continue

            target_states = set(state_set) - covered
            if not target_states:
                continue

            covered |= target_states
            graph, invalid = modify_matrix_hard(
                graph, label_matrix, target_states, action, strategy_index, agents, state_to_idx
            )

            if invalid:
                reason = (
                    f"Strategia NON ammissibile (HARD): regola ({condition_norm} -> {action}) "
                    f"si applica a {sorted(target_states)} ma svuota la riga in {sorted(invalid)}. "
                    f"Quindi '{action}' non è abilitata lì."
                )
                return None, reason

            print(f"new transition matrix: {graph} modified by agent {strategy_index}")

    return graph, ""


def pruning(cgs, model_path, agents, formula, current_agents):
    """
    Ritorna (ok: bool, reason: str)
    - ok=True se dopo pruning il model checking della formula sul modello potato è True da s0
    - ok=False e reason spiega:
        * strategia non ammissibile (righe svuotate)
        * modello potato invalido
        * formula non soddisfatta
    """
    cgs1 = CGS()
    cgs1.read_file(model_path)

    pruned_graph, reason = process_transition_matrix_data(cgs, model_path, agents, *current_agents)
    if pruned_graph is None:
        return False, reason

    cgs1.graph = pruned_graph

    # validate (se la tua matrixParser controlla righe tutte-0, qui esploderebbe: meglio catturare)
    try:
        cgs1.matrixParser(cgs.get_number_of_agents())
    except Exception as e:
        return False, f"Pruned model invalid: {e}"

    cgs1.write_updated_file(model_path, cgs1.graph, pruned_model_file)

    # robust su firme diverse
    try:
        result = model_checking(cgs1, formula, pruned_model_file)
    except TypeError:
        result = model_checking(formula, pruned_model_file)

    init_res = result.get("initial_state", "")
    print(init_res or result)

    if init_res == "Initial state s0: True":
        return True, ""

    return False, f"Formula non soddisfatta nello stato iniziale: {init_res}"

