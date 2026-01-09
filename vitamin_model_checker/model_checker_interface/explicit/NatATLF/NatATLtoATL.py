import re


def natatl_to_atl(natatl_formula):
    # Regex to match the coalition pattern with complexity bound
    k_pattern = r'<\{((?:\d+,)*\d+)\},\s*\d+>'

    # Function to remove complexity bound and curly brackets
    def replace_match(match):
        coalition = match.group(1)  # Get the agents inside the curly brackets
        return f'<{coalition}>'  # Return without complexity bound and brackets

    # Substitute the pattern using the helper function
    atl_formula = re.sub(k_pattern, replace_match, natatl_formula)

    return atl_formula


# Test cases
if __name__ == "__main__":
    test_cases = [
        "<{1,2},4>Xa",
        "!<{3},2>Fq",
        "<{1,2,3},5>G(r → p)",
        "<{1},1>X(p ∧ q)",
    ]

    # Convert NatATL formulas to ATL
    converted = [natatl_to_atl(tc) for tc in test_cases]

    for i, result in enumerate(converted):
        print(f"NatATL: {test_cases[i]} -> ATL: {result}")
