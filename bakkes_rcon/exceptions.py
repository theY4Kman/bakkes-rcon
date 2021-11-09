__all__ = [
    'BakkesRconError',
    'NotConnectedError',
    'AuthenticationError',
]


class BakkesRconError(Exception):
    """Base for all bakkes-rcon errors"""


class NotConnectedError(BakkesRconError):
    """Bakkes RCON Client is not connected to the server"""


class AuthenticationError(BakkesRconError, ValueError):
    """The client could not authenticate with the server

    This usually means the password is incorrect
    """
