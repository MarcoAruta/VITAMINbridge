from vitamin_model_checker.model_checker_interface.explicit.CTL import model_checking
from vitamin_model_checker.models.CGS import *
import re
import ast

pruned_model_file = "./tmp.txt"


def modify_matrix(graph, label_matrix, states, action, agent_index, agents):
    new_graph = [row.copy() for row in graph]

    for i, row in enumerate(new_graph):
        for j, elem in enumerate(row):
            if label_matrix[i][j] in states:
                if isinstance(elem, str) and elem != "*":
                    elem_parts = elem.split(",")
                    new_elem_parts = []

                    idx = agents[agent_index - 1] - 1  # posizione agente nella joint-action

                    for part in elem_parts:
                        part_list = list(part)

                        # Semantica "permissiva": tengo sia l'azione scelta sia Idle
                        if part_list[idx] == "I" or part_list[idx] == action:
                            new_elem_parts.append(part)

                    new_graph[i][j] = ",".join(new_elem_parts) if new_elem_parts else 0

    return new_graph


def normalize_ctl_condition(cond: str) -> str:
    if cond is None:
        return ""
    s = str(cond)

    s = s.replace("∧", "&").replace("∨", "|").replace("¬", "!").replace("→", ">")
    s = re.sub(r"\bnot\b", "!", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def process_transition_matrix_data(cgs, model, agents, *strategies):
    graph = cgs.get_graph()
    label_matrix = cgs.create_label_matrix(graph)
    all_states = set(cgs.get_states())

    print(f"initial transition matrix: {graph}")

    actions_per_agent = cgs.get_actions(agents)
    for agent_key, acts in actions_per_agent.items():
        print(f"actions_{agent_key}")
        print(acts)

    for strategy_index, strategy in enumerate(strategies, start=1):
        covered = set()

        for (condition, action) in strategy["condition_action_pairs"]:
            condition = str(condition).strip()

            # --- caso T: default sugli stati rimanenti ---
            if condition.upper() == "T":
                target_states = all_states - covered
                if not target_states:
                    continue
                covered |= target_states
                graph = modify_matrix(graph, label_matrix, target_states, action, strategy_index, agents)
                print(f"[T] new transition matrix: {graph} modified by agent {strategy_index}")
                continue

            # --- CTL normale ---
            condition_norm = normalize_ctl_condition(condition)
            states = model_checking(cgs, condition_norm, model)

            if not isinstance(states, dict) or "res" not in states:
                print(f"[WARN] CTL returned unexpected (no dict/res) for '{condition_norm}': {states}")
                continue

            res_str = states.get("res", "")
            if ": " not in res_str:
                print(f"[WARN] CTL res has no ': ' for '{condition_norm}': {states}")
                continue

            try:
                state_set = ast.literal_eval(res_str.split(": ", 1)[1])
            except Exception as e:
                print(f"[WARN] cannot parse CTL result for '{condition_norm}': {res_str} ({e})")
                continue

            if not state_set:
                continue

            target_states = set(state_set) - covered
            if not target_states:
                continue

            covered |= target_states
            graph = modify_matrix(graph, label_matrix, target_states, action, strategy_index, agents)
            print(f"new transition matrix: {graph} modified by agent {strategy_index}")

    return graph


def pruning(cgs, model, agents, formula, current_agents):
    cgs1 = CGS()
    cgs1.read_file(model)

    cgs1.graph = process_transition_matrix_data(cgs, model, agents, *current_agents)
    cgs1.matrixParser(cgs.get_number_of_agents())
    cgs1.write_updated_file(model, cgs1.graph, pruned_model_file)

    # robust su firme diverse
    try:
        result = model_checking(cgs1, formula, pruned_model_file)
    except TypeError:
        result = model_checking(formula, pruned_model_file)

    print(result.get("initial_state", result))

    if result.get("initial_state") == "Initial state s0: True":
        print("I AM HERE")
        return True

    return False
