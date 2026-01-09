def matrixParser(matrix, n):
    for row in matrix:
        if all(elem == 0 for elem in row):
            raise ValueError("All row elements are 0")

        char_I_count = [0] * n

        for elem in row:
            if elem == 0:
                continue

            strings = str(elem).split(',')
            for s in strings:
                #if len(s) != n:
                #    raise ValueError(f"string length {s} for element {elem} is not equal to {n}")

                for i in range(n):
                    if s[i] == 'I':
                        char_I_count[i] += 1

        if any(count == 0 for count in char_I_count):
            raise ValueError("Idle error: There has to be at least one 'I' for each row")

# Use Example
#matrix = [['III', 0, 0, 0], [0, 'IIZ', 'ADZ,BDZ', 'ACZ,BCI'], ['ACZ,BDZ', 'ICZ', 'III', 'ADZ,BCZ'], [0, 'CIZ', 0, 'III']]
#n = 3
#parser(matrix, n)

def matrixParserforTree(matrix, n):
    has_nonzero_transition_from_s0 = False

    for i, row in enumerate(matrix):
        if all(elem == 0 for elem in row):
            raise ValueError("All row elements are 0")

        char_I_count = [0] * n

        for elem in row:
            if elem == 0:
                continue

            strings = str(elem).split(',')
            for s in strings:
                #if len(s) != n:
                #    raise ValueError(f"string length {s} for element {elem} is not equal to {n}")

                for j in range(n):
                    if s[j] == 'I':
                        char_I_count[j] += 1

        if any(count == 0 for count in char_I_count):
            raise ValueError("Idle error: There has to be at least one 'I' for each row")

        if i == 0 and any(elem != 0 for elem in row):
            has_nonzero_transition_from_s0 = True

    if not has_nonzero_transition_from_s0:
        raise ValueError("Transition error: The initial state 's0' must have at least one non-zero transition")

    for i, row in enumerate(matrix):
        #Tree uniqueness condition: We cannot deal with forests (example: if s0 has not any transition towards s1 and s1 has its own trasition towards s0, than it means that it belongs to a different tree where s1 is root, so model is a forest)
        if i != 0 and any(elem != 0 for elem in row) and all(matrix[0][j] == 0 for j in range(len(matrix[0])) if j != 0):
            raise ValueError(f"Configuration error: State 's0' has no transitions to other states but state 's{i}' has transitions.")



# Use Example
#matrix = [['III', 0, 0, 0], [0, 'IIZ', 'ADZ,BDZ', 'ACZ,BCI'], ['ACZ,BDZ', 'ICZ', 'III', 'ADZ,BCZ'], [0, 'CIZ', 0, 'III']]
#n = 3
#matrixParserforTree(matrix, n)
