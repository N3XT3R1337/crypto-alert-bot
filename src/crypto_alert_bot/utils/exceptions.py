class CryptoAlertBotError(Exception):
    def __init__(self, message: str = "An error occurred in CryptoAlertBot") -> None:
        self.message = message
        super().__init__(self.message)


class ExchangeAPIError(CryptoAlertBotError):
    def __init__(self, exchange: str, detail: str = "") -> None:
        self.exchange = exchange
        message = f"Exchange API error [{exchange}]: {detail}"
        super().__init__(message)


class InvalidSymbolError(CryptoAlertBotError):
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        message = f"Invalid trading symbol: {symbol}"
        super().__init__(message)


class AlertLimitExceededError(CryptoAlertBotError):
    def __init__(self, user_id: int, limit: int) -> None:
        self.user_id = user_id
        self.limit = limit
        message = f"User {user_id} exceeded alert limit of {limit}"
        super().__init__(message)


class CacheConnectionError(CryptoAlertBotError):
    def __init__(self, detail: str = "") -> None:
        message = f"Redis cache connection error: {detail}"
        super().__init__(message)


class DatabaseError(CryptoAlertBotError):
    def __init__(self, operation: str, detail: str = "") -> None:
        self.operation = operation
        message = f"Database error during {operation}: {detail}"
        super().__init__(message)


class ChartGenerationError(CryptoAlertBotError):
    def __init__(self, symbol: str, detail: str = "") -> None:
        self.symbol = symbol
        message = f"Chart generation failed for {symbol}: {detail}"
        super().__init__(message)


class ConfigurationError(CryptoAlertBotError):
    def __init__(self, key: str) -> None:
        self.key = key
        message = f"Missing or invalid configuration: {key}"
        super().__init__(message)
