import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any

# IMPORTA le stesse funzioni usate per generare input.txt
from vitamin_model_checker.model_checker_interface.explicit.NatATL.bridge.jsonToTxt import (
    build_ap_symbol_map,
    build_action_code_map,
)


def load_json_robust(json_path: Path) -> Any:
    """
    Robust JSON loader tolerant to trailing commas / extra text after the last '}'.
    """
    raw = json_path.read_text(encoding="utf-8").strip()
    last_brace = raw.rfind("}")
    if last_brace == -1:
        raise ValueError("Invalid JSON: no closing '}' found")
    raw = raw[: last_brace + 1].rstrip()
    raw = re.sub(r",\s*\Z", "", raw)
    return json.loads(raw)


def parse_coalition_agents(formula_natatl: str) -> List[str]:
    """
    Extract coalition agents from: <{a,b,c}, k> ...
    """
    if not formula_natatl:
        return []
    m = re.search(r"<\s*\{\s*([^}]*)\s*\}\s*,", formula_natatl)
    if not m:
        return []
    inside = m.group(1).strip()
    if not inside:
        return []
    return [x.strip() for x in inside.split(",") if x.strip()]


def translate_text_with_aps(text: str, ap_symbol: Dict[str, str]) -> str:
    """
    Replace AP names with their symbols (whole-token only).
    Works for both formula and conditions.
    AP symbols are expected to be lowercase (from build_ap_symbol_map).
    """
    if text is None:
        return ""
    text = str(text).strip()

    for ap in sorted(ap_symbol.keys(), key=len, reverse=True):
        sym = ap_symbol[ap]
        text = re.sub(r"\b" + re.escape(ap) + r"\b", sym, text)

    return text


def convert_strategy_json_to_txt(
    json_path: str | Path,
    out_path: str | Path,
    coalition_from_formula: bool = True,
    ensure_total_with_idle: bool = False,
) -> List[dict]:
    """
    Converts output.strategy_natural into txt format:
      [{'condition_action_pairs': [('a','P'), ('T','I')]}]
    one dict per coalition agent (order: as in formula coalition, if parseable).

    Rules:
    - NON ignora più 'T': la mantiene come condizione speciale.
      (così pruning la può usare per coprire gli stati rimanenti)
    - Conditions use the SAME AP symbols of input.txt (lowercase)
    - Actions use the SAME action-code policy of input.txt (uppercase)
    - (optional) if ensure_total_with_idle=True and no 'T' rule is provided,
      append ('T','I') as default.
    """
    json_path = Path(json_path)
    out_path = Path(out_path)

    data = load_json_robust(json_path)
    inp = data["input"] if isinstance(data, dict) and "input" in data else data
    out = data.get("output", {}) if isinstance(data, dict) else {}

    states = inp["states"]
    agents = inp["agents"]
    actions_by_agent = inp["actions"]
    labeling = inp.get("labeling", {})
    formula_raw = str(inp.get("formula_natatl", "")).strip()

    #strategy_natural = out.get("strategy_natural", {}) or {}

    strategy_natural = {}
    if isinstance(out, dict):
        strategy_natural = out.get("strategy_natural", {}) or {}

    # fallback: json = givenStrategy.json
    if not strategy_natural and isinstance(data, dict):
        strategy_natural = data.get("strategy_natural", {}) or {}

    # coalition = from formula or fallback to strategy agents
    coalition: List[str] = []
    if coalition_from_formula:
        coalition = parse_coalition_agents(formula_raw)
    if not coalition:
        coalition = list(strategy_natural.keys())

    # IMPORTANT: use the EXACT same AP/action mappings as input.txt converter
    _, ap_symbol = build_ap_symbol_map(states, labeling)             # ap_symbol is lowercase
    action_code = build_action_code_map(agents, actions_by_agent)    # action symbols are uppercase

    result: List[dict] = []

    for ag in coalition:
        pairs: List[Tuple[str, str]] = []
        rules = strategy_natural.get(ag, []) or []

        has_T_rule = False

        for r in rules:
            cond = str(r.get("cond", "")).strip()
            act = str(r.get("action", "")).strip()

            # --- cond translation ---
            if cond.upper() == "T":
                # T è costante vera: NON va tradotta con AP symbols
                cond_t = "T"
                has_T_rule = True
            else:
                cond_t = translate_text_with_aps(cond, ap_symbol)  # lowercase symbols

            # --- action translation ---
            if ag in action_code and act in action_code[ag]:
                act_t = action_code[ag][act]
            else:
                # conservative fallback (still uppercase)
                letters = [c for c in act if c.isalpha()]
                act_t = (letters[0].upper() if letters else act[:1].upper() or "A")

            pairs.append((cond_t, act_t))

        # Optional: ensure total strategy by adding (T,I) if missing
        if ensure_total_with_idle and not has_T_rule:
            pairs.append(("T", "I"))

        result.append({"condition_action_pairs": pairs})

    out_path.write_text(repr(result) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    base = Path(__file__).parent
    convert_strategy_json_to_txt(
        base / "input.json",
        base / "strategy.txt",
        coalition_from_formula=True,
        ensure_total_with_idle=False,  # metti True se vuoi auto-aggiungere (T,I)
    )
    print("Written:", base / "strategy.txt")
