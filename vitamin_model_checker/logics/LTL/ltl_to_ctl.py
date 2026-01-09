import re

def ltl_to_ctl(ltl_formula):
    # Adds "A" in front of temporal operators X, F e G
    ltl_formula = re.sub(r'(?<!A)([XFG])', r'A\1', ltl_formula)

    # Handles Until (U) operator adding "A" outer the involved formula
    ltl_formula = re.sub(r'([a-zA-Z]\w*)U([a-zA-Z]\w*)', r'A(\1U\2)', ltl_formula)

    return ltl_formula

#print(ltl_to_ctl("Xp"))      # Output: AXp
#print(ltl_to_ctl("FGp"))     # Output: AFAGp
#print(ltl_to_ctl("pUq"))     # Output: A(pUq)
#print(ltl_to_ctl("G(XpUq)")) # Output: AG(A(XpUq))
