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