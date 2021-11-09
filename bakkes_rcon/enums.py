from enum import Enum

__all__ = ['StrEnum']


class StrEnum(str, Enum):
    #: Longest length of item value
    max_length: int

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls.max_length = 0

    def __init__(self, *args):
        if (value_len := len(self._value_)) > self.max_length:
            self.max_length = value_len

    def __str__(self) -> str:
        return self._value_

    def __hash__(self) -> int:
        return hash(self._value_)


class PrettyStrEnum(StrEnum):
    """Allows enum items to declare a pretty string

    >>> class Apple(PrettyStrEnum):
    ...     RED_DELICIOUS = 'red-delicious', 'Red Delicious'
    ...     HONEYCRISP = 'honeycrisp'  # defaults to titleized
    ...
    >>> str(Apple.RED_DELICIOUS)
    'red-delicious'
    >>> Apple.RED_DELICIOUS.pretty
    'Red Delicious'
    >>> Apple.HONEYCRISP.pretty
    'Honeycrisp'

    >>> class AutoPrettyApple(PrettyStrEnum):
    ...     RED_DELICIOUS = 'red-delicious'
    ...     HONEYCRISP = 'honeycrisp'
    ...
    ...     @classmethod
    ...     def _prettify_value(cls, value):
    ...         return value.replace('-', ' ').title()
    ...
    >>> AutoPrettyApple.RED_DELICIOUS.pretty
    'Red Delicious'
    """

    pretty: str

    #: Longest length of item pretty strings
    pretty_max_length: int

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls.pretty_max_length = 0

    def __init__(self, *args):
        super().__init__(*args)
        if (pretty_len := len(self.pretty)) > self.pretty_max_length:
            self.pretty_max_length = pretty_len

    def __new__(cls, value: str, pretty: str = None, **kwargs):
        item = str.__new__(cls)
        item._value_ = value

        if pretty is None:
            pretty = cls._prettify_value(value)
        item.pretty = pretty

        return item

    @classmethod
    def _prettify_value(cls, value: str) -> str:
        """Convert an enum value to its pretty string form"""
        return value.title()
