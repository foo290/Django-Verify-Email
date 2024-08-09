class UserAlreadyActive(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class MaxRetriesExceeded(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class UserNotFound(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidToken(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidTokenOrEmail(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class WrongTimeInterval(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
