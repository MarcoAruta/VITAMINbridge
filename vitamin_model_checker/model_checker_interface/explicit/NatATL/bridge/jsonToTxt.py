import json
from collections import defaultdict
from pathlib import Path
import re
import string

DEFAULT_UNKNOWN_TRANSITION_BY = """Unkown_Transition_by
0 0 0 0 0 0 0 0
0 0 t1 0 0 0 0 0
0 0 0 c 0 0 0 0
0 0 0 0 0 0 0 0
0 0 0 0 0 t1 0 0
0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0
""".rstrip()


def _pick_unique_char(preferred_chars, used):
    for ch in preferred_chars:
        ch = ch.upper()
        if ch.isalnum() and ch not in used:
            used.add(ch)
            return ch
    for ch in string.ascii_uppercase:
        if ch not in used:
            used.add(ch)
            return ch
    raise RuntimeError("Finite alphabet exhausted while assigning codes.")


def _pick_unique_letter_lower(preferred_chars, used):
    for ch in preferred_chars:
        ch = ch.lower()
        if ch.isalnum() and ch not in used:
            used.add(ch)
            return ch
    for ch in string.ascii_lowercase:
        if ch not in used:
            used.add(ch)
            return ch
    raise RuntimeError("Finite alphabet exhausted while assigning AP symbols.")


def build_action_code_map(agents, actions_by_agent):
    """
    Returns: dict agent -> dict action -> single-char code (UPPERCASE)
    Policy:
    - First alphabetic char found in the action string (uppercased)
    - If collision within the same agent, try subsequent alphabetic chars
    - Fallback to any unused A-Z
    """
    code_map = {}
    for ag in agents:
        used = set()
        m = {}
        for act in actions_by_agent[ag]:
            act_str = str(act).strip()
            preferred = [c for c in act_str if c.isalpha()]
            if not preferred:
                preferred = [c for c in act_str if c.isalnum()]
            m[act] = _pick_unique_char(preferred, used)
        code_map[ag] = m
    return code_map


def build_ap_symbol_map(states, labeling_dict):
    """
    Collects APs preserving order of appearance across states,
    then assigns short symbols as SINGLE-CHAR **lowercase** (to avoid confusion with actions).
    Returns: (aps_list, symbol_map)
    """
    aps = []
    seen = set()
    for s in states:
        for ap in labeling_dict.get(s, []):
            if ap not in seen:
                seen.add(ap)
                aps.append(ap)

    used = set()
    symbol_map = {}
    for ap in aps:
        preferred = []
        tokens = re.split(r"[_\-\s]+", ap.strip())
        if tokens and tokens[0]:
            preferred.append(tokens[0][0])
        preferred.extend([c for c in ap if c.isalpha()])
        symbol_map[ap] = _pick_unique_letter_lower(preferred, used)

    return aps, symbol_map


def translate_formula_aps(formula: str, ap_symbol: dict) -> str:
    """
    Replace occurrences of AP names in the NatATL formula with their short symbols.
    Replaces whole tokens only (word boundary).
    """
    if not formula:
        return ""

    for ap in sorted(ap_symbol.keys(), key=len, reverse=True):
        sym = ap_symbol[ap]
        formula = re.sub(r"\b" + re.escape(ap) + r"\b", sym, formula)

    return formula


def _ensure_all_agents_can_idle_on_diagonal(states, agents, action_code, cells, cell_seen):
    """
    Robustness constraint (as requested):

    For each diagonal cell (s -> s), if among the joint-actions listed there is NOT
    at least one transition where EVERY agent plays 'I' in its position (e.g., for 2 agents: 'II'),
    then we add that joint code to the diagonal.

    This matches your desired behavior:
      diagonal: IS  -> becomes IS,II
    """
    idle_joint_code = "I" * len(agents)

    for s in states:
        # already present?
        if idle_joint_code in cell_seen[(s, s)]:
            continue

        # add it
        cell_seen[(s, s)].add(idle_joint_code)
        cells[(s, s)].append(idle_joint_code)


def json_to_tool_txt(json_path: str, out_path: str, formula_out_path: str | None = None):
    """
    Reads JSON from json_path and writes the tool .txt to out_path.
    If formula_out_path is provided, writes the NatATL formula with translated APs.

    Supports either:
      - root has keys input/output/metadata (your example), OR
      - root is directly the 'input' object
    """
    raw = Path(json_path).read_text(encoding="utf-8").strip()

    # Robust: tolerate trailing comma / extra text after last closing brace
    last_brace = raw.rfind("}")
    if last_brace == -1:
        raise ValueError("Invalid JSON: no closing '}' found")
    raw = raw[: last_brace + 1].rstrip()
    raw = re.sub(r",\s*\Z", "", raw)

    data = json.loads(raw)
    inp = data["input"] if isinstance(data, dict) and "input" in data else data

    states = inp["states"]
    agents = inp["agents"]
    actions_by_agent = inp["actions"]
    transitions = inp["transitions"]
    initial_state = inp["initial_state"]
    labeling = inp.get("labeling", {})

    # 1) Build action-code map and convert transitions into matrix cells
    action_code = build_action_code_map(agents, actions_by_agent)

    cells = defaultdict(list)
    cell_seen = defaultdict(set)

    def add_joint(fr, to, joint_actions):
        joint_code = "".join(action_code[ag][act] for ag, act in zip(agents, joint_actions))
        if joint_code not in cell_seen[(fr, to)]:
            cell_seen[(fr, to)].add(joint_code)
            cells[(fr, to)].append(joint_code)

    for t in transitions:
        add_joint(t["from"], t["to"], t["joint"])

    # 2) Robust diagonal idle constraint: add "II...I" if missing on each diagonal cell
    _ensure_all_agents_can_idle_on_diagonal(states, agents, action_code, cells, cell_seen)

    # 3) Build matrix text
    matrix_lines = []
    for fr in states:
        row = []
        for to in states:
            row.append(",".join(cells[(fr, to)]) if cells[(fr, to)] else "0")
        matrix_lines.append(" ".join(row))

    # 4) Atomic propositions + labeling matrix (AP symbols are lowercase)
    aps, ap_symbol = build_ap_symbol_map(states, labeling)
    ap_symbols_in_order = [ap_symbol[ap] for ap in aps]

    lab_lines = []
    for s in states:
        s_aps = set(labeling.get(s, []))
        bits = ["1" if ap in s_aps else "0" for ap in aps]
        lab_lines.append(" ".join(bits))

    # 4b) Write translated NatATL formula (APs translated to lowercase symbols)
    if formula_out_path is not None:
        formula_raw = str(inp.get("formula_natatl", "")).strip()

        # 1) traduci AP -> simboli minuscoli
        formula_translated = translate_formula_aps(formula_raw, ap_symbol)

        # 2) traduci coalizione nomi -> indici 1-based
        formula_translated = translate_formula_coalition_to_indices(formula_translated, agents)

        # 3) compattazione finale
        formula_translated = compact_natatl_formula(formula_translated)

        Path(formula_out_path).write_text(formula_translated + "\n", encoding="utf-8")

    # 5) Compose tool file
    out = []
    out.append("Transition")
    out.extend(matrix_lines)
    out.append(DEFAULT_UNKNOWN_TRANSITION_BY)
    out.append("Name_State")
    out.append(" ".join(states))
    out.append("Initial_State")
    out.append(initial_state)
    out.append("Atomic_propositions")
    out.append(" ".join(ap_symbols_in_order))
    out.append("Labelling")
    out.extend(lab_lines)
    out.append("Number_of_agents")
    out.append(str(len(agents)))

    Path(out_path).write_text("\n".join(out) + "\n", encoding="utf-8")

    return {
        "action_code_map": action_code,
        "ap_symbol_map": ap_symbol,
        "aps_order": aps,
    }


def translate_formula_coalition_to_indices(formula: str, agents_in_model: list[str]) -> str:
    """
    Converts coalition agent names to 1-based indices according to agents_in_model order.

    Example:
      agents_in_model = ["robot_arm","conveyor"]
      "<{robot_arm}, 2> F j" -> "<{1}, 2> F j"
      "<{conveyor, robot_arm}, 2> ..." -> "<{2,1}, 2> ..."
    If coalition already numeric, leaves it as is.
    """
    if not formula:
        return ""

    m = re.search(r"<\s*\{\s*([^}]*)\s*\}\s*,", formula)
    if not m:
        return formula  # leave untouched if unexpected format

    inside = m.group(1).strip()
    if not inside:
        return formula

    items = [x.strip() for x in inside.split(",") if x.strip()]
    if not items:
        return formula

    # already numeric?
    if all(re.fullmatch(r"\d+", it) for it in items):
        return formula

    # map names -> indices
    name_to_idx = {name: i + 1 for i, name in enumerate(agents_in_model)}
    mapped = []
    for name in items:
        if name not in name_to_idx:
            raise ValueError(f"Agent '{name}' not found in input.agents={agents_in_model}")
        mapped.append(str(name_to_idx[name]))

    # replace only the coalition content between { }
    start, end = m.span(1)
    return formula[:start] + ",".join(mapped) + formula[end:]


def compact_natatl_formula(formula: str) -> str:
    """
    Removes unnecessary spaces from a NatATL formula.

    Example:
      "<{1}, 2> F j"  -> "<{1},2>Fj"
      "! <{1,2}, 3> G p" -> "!<{1,2},3>Gp"
    """
    if not formula:
        return ""

    # remove spaces around key symbols
    formula = re.sub(r"\s+", "", formula)
    return formula


if __name__ == "__main__":
    base = Path(__file__).parent
    info = json_to_tool_txt(
        base / "exampleinput.json",
        base / "input.txt",
        base / "formula.txt",
    )

    print("Written:", base / "input.txt")
    print("Written:", base / "formula.txt")
    print("Action codes:", info["action_code_map"])
    print("AP symbols:", info["ap_symbol_map"])


