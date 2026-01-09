from vitamin_model_checker.model_checker_interface.explicit.NatATL.Memoryless.strategies import (
    initialize, generate_strategies, generate_guarded_action_pairs
)
from vitamin_model_checker.model_checker_interface.explicit.NatATL.Memoryless.pruning import pruning
from vitamin_model_checker.model_checker_interface.explicit.NatATL.bridge.jsonToTxt import json_to_tool_txt
from pathlib import Path
import json
from vitamin_model_checker.model_checker_interface.explicit.NatATL.bridge.strategyJsonToTxt import convert_strategy_json_to_txt


def model_checking(model: dict):
    base_bridge = Path(__file__).resolve().parents[1] / "bridge"

    # <-- QUI scegli quali file usare nel bridge
    MODEL_JSON_NAME = "exampleinput.json"
    STRATEGY_JSON_NAME = "examplestrategy.json"

    json_tmp = base_bridge / MODEL_JSON_NAME  # invece di input2.json
    input_txt = base_bridge / "input.txt"
    formula_txt = base_bridge / "formula.txt"

    output_path = Path(__file__).resolve().parent / "output.txt"

    # --- normalize model input (filename path OR UploadedFile OR dict) ---
    if isinstance(model, (str, Path)):
        raw = Path(model).read_text(encoding="utf-8")
        model_dict = json.loads(raw)
    elif hasattr(model, "getvalue"):
        raw = model.getvalue()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        model_dict = json.loads(raw)
    elif isinstance(model, dict):
        model_dict = model
    else:
        raise TypeError(f"Unsupported model type: {type(model)}")

    # mantengo SOLO il modello
    if isinstance(model_dict, dict) and "input" in model_dict:
        model_only = {"input": model_dict["input"]}
    else:
        model_only = {"input": model_dict}

    # scrive nel file scelto (exampleinput.json)
    json_tmp.write_text(json.dumps(model_only, ensure_ascii=False, indent=2), encoding="utf-8")

    # convert model once
    json_to_tool_txt(json_tmp, input_txt, formula_txt)

    # 3) leggi la formula da file (STRINGA)
    formula = formula_txt.read_text(encoding="utf-8").strip()

    # init once
    k, agent_actions, actions_list, atomic_propositions, CTLformula, agents, cgs = initialize(input_txt, formula)

    # qui scegli la strategia da file scelto (examplestrategy.json)
    strategy_iter = one_strategy_provider(base_bridge, STRATEGY_JSON_NAME)

    found_solution = False
    last_reason = ""  # <-- per salvare la motivazione dell'ultimo tentativo
    result = {}
    attempt = 0

    for given_strategy_path in strategy_iter:
        attempt += 1

        current_agents = bundle_and_convert_strategy(json_tmp, given_strategy_path, base_bridge)
        print(f"[Attempt {attempt}] strategy under exam: {current_agents}")

        # >>> MODIFICA CHIAVE: pruning ora ritorna (ok, reason)
        ok, reason = pruning(cgs, str(input_txt), agents, CTLformula, current_agents)
        found_solution = ok
        last_reason = reason or last_reason

        if found_solution:
            result["Satisfiability"] = True
            result["Attempt"] = attempt
            result["Winning Strategy per agent"] = current_agents
            write_output_file(output_path, result)
            return result

        if attempt >= k:
            break

    # no solution
    print(f"False, no states satisfying {CTLformula} have been found!")

    result["Satisfiability"] = False
    result["Complexity Bound"] = k
    result["Attempt"] = attempt
    if last_reason:
        result["Reason"] = last_reason  # <-- la motivazione finisce in output.txt

    write_output_file(output_path, result)
    return result


def bundle_and_convert_strategy(model_json_path: Path, given_strategy_path: Path, base_bridge: Path):
    tmp_bundle_path = base_bridge / "_tmp_bundle_with_strategy.json"
    strategy_txt_path = base_bridge / "strategy.txt"

    model_bundle = json.loads(model_json_path.read_text(encoding="utf-8"))

    # examplestrategy.json / givenStrategy.json contiene almeno {"strategy_natural": {...}}
    given = json.loads(given_strategy_path.read_text(encoding="utf-8"))
    given_strategy_natural = given.get("strategy_natural", {})

    if "input" not in model_bundle:
        model_bundle = {"input": model_bundle, "output": {}}
    model_bundle.setdefault("output", {})
    model_bundle["output"]["strategy_natural"] = given_strategy_natural

    tmp_bundle_path.write_text(json.dumps(model_bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    # returns list[dict] per-agent (what pruning expects)
    current_agents = convert_strategy_json_to_txt(tmp_bundle_path, strategy_txt_path)
    return current_agents


def one_strategy_provider(base_bridge: Path, filename: str):
    yield base_bridge / filename


def write_output_file(output_path: Path, result: dict):
    lines = []

    if result.get("Satisfiability"):
        lines.append("Satisfiable: True")
        if "Attempt" in result:
            lines.append(f"Attempt: {result['Attempt']}")
        if "Winning Strategy per agent" in result:
            lines.append("Winning Strategy per agent:")
            lines.append(str(result["Winning Strategy per agent"]))
    else:
        lines.append("Satisfiable: False")
        if "Complexity Bound" in result:
            lines.append(f"Complexity Bound: {result['Complexity Bound']}")
        if "Attempt" in result:
            lines.append(f"Attempt: {result['Attempt']}")
        if "Reason" in result:
            lines.append("Reason:")
            lines.append(str(result["Reason"]))

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
