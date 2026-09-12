class EndToken:
    def nud(self, parser: object) -> "EndToken":
        return self


EndToken = EndToken()


class UnusedToken:
    pass


def parse() -> EndToken:
    return EndToken
