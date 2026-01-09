class Parser:
    def __init__(self, input):
        self.tokens = input.split()
        self.current_token = None
        self.next()

    def next(self):
        if len(self.tokens) == 0:
            self.current_token = None
        else:
            self.current_token = self.tokens.pop(0)

    def parse_expression(self):
        result = self.parse_implies_expression()
        while self.current_token == 'iff':
            self.next()
            result = f"({result} iff {self.parse_implies_expression()})"
        return result

    def parse_implies_expression(self):
        result = self.parse_or_expression()
        while self.current_token == 'implies':
            self.next()
            result = f"({result} implies {self.parse_or_expression()})"
        return result

    def parse_or_expression(self):
        result = self.parse_and_expression()
        while self.current_token == 'or':
            self.next()
            result = f"({result} or {self.parse_and_expression()})"
        return result

    def parse_and_expression(self):
        result = self.parse_unary_expression()
        while self.current_token == 'and':
            self.next()
            result = f"({result} and {self.parse_unary_expression()})"
        return result

    def parse_unary_expression(self):
        if self.current_token == 'not':
            self.next()
            return f"(not {self.parse_term()})"
        else:
            return self.parse_term()

    def parse_term(self):
        term = self.current_token
        self.next()
        return term

def parse_string(input_str):
    parser = Parser(input_str)
    return parser.parse_expression()