class RegexWitnessGenerator:
    def __init__(self, pattern, length):
        # Initialize class using the original pattern and the desired length
        self.original_pattern = pattern
        self.length = length
        # Divides pattern in groups, keeping also '*' and '.'
        self.groups = self._split_groups_by_star(pattern)
        # Set to keep track of the upcoming generated combinations
        self.generated = set()
        # Generates all possible combinations of witness words
        self._generate_combinations()

    def _split_groups_by_star(self, pattern):
        # Function to divide pattern in groups separated by '*' or '.'
        groups = []
        buffer = []
        for char in pattern:
            if char == '*' or char == '.':
                if char == '*':
                    if buffer:
                        # Adds the current group to the final until *
                        groups.append(''.join(buffer) + '*')
                        buffer = []
                else:
                    if buffer:
                        # Does the same but removing "." as we add it in another function
                        groups.append(''.join(buffer) + '')
                        buffer = []
            else:
                # Adds the current character to the buffer
                buffer.append(char)
        if buffer:
            # Adds the last group to the final group
            groups.append(''.join(buffer))
        return groups

    def _generate_combinations(self):
        # Initialize the list of combinations
        self.combinations = []
        # Starts backtracking to generate all possible combinations
        self._backtrack([], 0)

    def _backtrack(self, current, pos):
        # If we reached the end of groups (so we formed a word), check if the length is right
        if pos >= len(self.groups):
            if len(current) == self.length:
                # Add the current combination to the list of combinations with spaces around dots
                self.combinations.append(' . '.join(current))
            return

        group = self.groups[pos]
        if group.endswith('*'):
            # If group terminates with '*', repeat the current group
            base = group[:-1]
            remaining_length = self.length - len(current)
            for i in range(remaining_length + 1):
                self._backtrack(current + [base] * i, pos + 1)
        else:
            # otherwise (if it doesn't terminate with *), add the current group already
            if len(current) < self.length:
                self._backtrack(current + [group], pos + 1)

    def next_word(self):
        # Returns the next generated witness word
        while self.combinations:
            word = self.combinations.pop(0)
            if word not in self.generated:
                self.generated.add(word)
                return word
        return None

def store_word(word):
    # Split the string into substrings based on dots with spaces around them
    substrings = word.split(' . ')

    # Initialize an empty list to store the final result
    result = []

    # Iterate over the substrings
    for substring in substrings:
        # Remove leading and trailing whitespaces
        substring = substring.strip()
        # Add the substring to the result list
        result.append(substring)

    return result

# Use case
pattern = "a and b.q*"
length = 3
generator = RegexWitnessGenerator(pattern, length)

word = ""
while word is not None:
    word = generator.next_word()
    if word:
        print(word)
        print(type(word))
        res = store_word(word)
        print(res)
        print(type(res[1]))
        print(len(res))









