from __future__ import annotations

from dataclasses import dataclass, field
from enum import EnumMeta
from functools import total_ordering
from typing import Any, Callable, ClassVar, Optional, Type, TypeVar

from bakkes_rcon.enums import PrettyStrEnum, StrEnum
from bakkes_rcon.types import RawInventoryItem

__all__ = [
    'Quality',
    'InventoryItem',
]

InventoryItem_t = TypeVar('InventoryItem_t', bound='InventoryItem')


###
# These are alternate names I've encountered being returned from bakkes. Their origin is
# uncertain; perhaps old items wear these strings? (I've been playing since '16)
#
# This dict maps them to the names returned by bakkesmod.dll's invent_dump and
# BetterInventoryExport
#
# Ref: https://gist.github.com/theY4Kman/466eb5e8cce2f488aae3baa2f36c1608
# Ref: https://github.com/Bakkes/BetterInventoryExport/blob/214fbafc0dd58126d1374809c6b62a18dc74b32f/BetterInventoryExport/BetterInventoryExport.h#L55-L66
#
QUALITY_ALT_NAMES: dict[str, str] = {
    'BlackMarket': 'Black market',
    'VeryRare': 'Very rare',
}


class QualityEnumMeta(EnumMeta):
    def __call__(cls, value, *args, **kwargs):
        if isinstance(value, str):
            value = QUALITY_ALT_NAMES.get(value, value)
        return super().__call__(value, *args, **kwargs)


@total_ordering
class Quality(PrettyStrEnum, metaclass=QualityEnumMeta):
    """Quality of an item

    This enum class is used to denormalize and uniquely identify the item qualities
    reported by Rocket League.

    The qualities are listed in order of rarity (except for Limited and Legacy, which
    don't really fit with any ordering), and may be used for sorting. The exact order
    is lifted from the BetterInventoryExport plugin that produces the inventory response.

    Ref: https://github.com/Bakkes/BetterInventoryExport/blob/214fbafc0dd58126d1374809c6b62a18dc74b32f/BetterInventoryExport/BetterInventoryExport.h#L8-L21
    """

    COMMON = 'Common'
    UNCOMMON = 'Uncommon'
    RARE = 'Rare'
    VERY_RARE = 'Very rare'
    IMPORT = 'Import'
    EXOTIC = 'Exotic'
    BLACK_MARKET = 'Black market'
    PREMIUM = 'Premium'
    LIMITED = 'Limited'
    LEGACY = 'Legacy'

    def __init__(self, *args):
        super().__init__(*args)
        self._sort_order_: int = len(self.__class__.__members__)

    def __int__(self) -> int:
        return self._sort_order_

    def __lt__(self, other: 'Quality' | str) -> bool:
        if isinstance(other, str):
            other = Quality(other)
        return int(self) < int(other)


class Slot(PrettyStrEnum):
    ANIMATED_DECAL = 'Animated Decal'
    ANTENNA = 'Antenna'
    AVATAR_BORDER = 'Avatar Border'
    BODY = 'Body'
    CRATE = 'Crate'
    DECAL = 'Decal'
    ENGINE_AUDIO = 'Engine Audio'
    GOAL_EXPLOSION = 'Goal Explosion'
    PAINT_FINISH = 'Paint Finish'
    PLAYER_ANTHEM = 'Player Anthem'
    PLAYER_BANNER = 'Player Banner'
    PLAYER_TITLE = 'Player Title'
    ROCKET_BOOST = 'Rocket Boost'
    TOPPER = 'Topper'
    TRAIL = 'Trail'
    WHEELS = 'Wheels'


class Paint(PrettyStrEnum):
    BLACK = 'Black'
    BURNT_SIENNA = 'Burnt Sienna'
    COBALT = 'Cobalt'
    CRIMSON = 'Crimson'
    FOREST_GREEN = 'Forest Green'
    GREY = 'Grey'
    LIME = 'Lime'
    ORANGE = 'Orange'
    PINK = 'Pink'
    PURPLE = 'Purple'
    SAFFRON = 'Saffron'
    SKY_BLUE = 'Sky Blue'
    TITANIUM_WHITE = 'Titanium White'


class CertificationType(PrettyStrEnum):
    AERIAL_GOALS = 'AerialGoals', 'Aerial Goals'
    ASSISTS = 'Assists'
    BACKWARDS_GOALS = 'BackwardsGoals', 'Backwards Goals'
    BICYCLE_GOALS = 'BicycleGoals', 'Bicycle Goals'
    CENTERS = 'Centers'
    CLEARS = 'Clears'
    EPIC_SAVES = 'EpicSaves', 'Epic Saves'
    GOALS = 'Goals'
    JUGGLES = 'Juggles'
    LONG_GOALS = 'LongGoals', 'Long Goals'
    MVPS = 'MVPs', 'MVPs'
    SAVES = 'Saves'
    SHOTS_ON_GOAL = 'ShotsOnGoal', 'Shots on Goal'
    TURTLE_GOALS = 'TurtleGoals', 'Turtle Goals'
    WINS = 'Wins'


class SpecialEdition(PrettyStrEnum):
    INVERTED = 'Edition_Inverted'
    HOLOGRAPHIC = 'Edition_Holographic'
    INFINITE = 'Edition_Infinite'

    @classmethod
    def _prettify_value(cls, value: str) -> str:
        return value.removeprefix('Edition_')


@dataclass(frozen=True)
class Certification:
    #: Stat type being tracked (e.g. backwards goals or MVPs)
    type: CertificationType

    #: Number of occurrences of the tracked stat
    value: int

    #: Base display name of the certification (e.g. Show-Off or Paragon)
    tag: str = field(init=False)

    #: Level 1-10, different for each type, describing magnitude of tracked stat values
    level: int = field(init=False)

    #: Adjective prepended to tag when displaying the certification, based on level
    #: NOTE: level 10 names replace the tag entirely in-game (e.g. Cold-Blooded or Unbeatable)
    level_name: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, 'tag', CERTIFICATION_TAGS[self.type])

        level_idx = next(
            n
            for n, lower_bound in reversed(tuple(enumerate(CERTIFICATION_LEVELS[self.type])))
            if self.value >= lower_bound
        )
        object.__setattr__(self, 'level', level_idx + 1)
        object.__setattr__(self, 'level_name', CERTIFICATION_LEVEL_NAMES[self.type][level_idx])

    def __str__(self) -> str:
        if self.level == 10:
            # The final level's name is always standalone
            return self.level_name

        return f'{self.level_name} {self.tag}'

    def full_str(self) -> str:
        return f'{self}: {self.value} {self.type.pretty}'


class InventoryItem:
    product_id: int = 0
    """
    ID of the base item
    """

    name: str = ''
    """
    Name of the item

    It appears in the case of blueprint items, this value appears to be the crate/series
    the blueprint item is from. To get the name of the item, regardless of whether it's
    a blueprint or not, use the `item_name` property.
    """

    slot: Slot | str = ''
    """
    Type of the item (e.g. Topper, Decal, Wheels, etc)
    """

    paint: Optional[Paint | str] = None
    """
    Colour of the item
    """

    certification: Optional[Certification] = None
    """
    A stat tracked when the item is worn (e.g. BackwardsGoals, Centers, Saves, etc)
    """

    certification_value: int = 0
    """
    Number of occurrences of certification stat events recorded while wearing the item
    """

    rank_label: Optional[str] = ''
    """
    Display name of item certification (e.g. Turtle, Tactician, Goalkeeper, etc)
    """

    quality: Quality = field(init=False)
    """
    Quality of the item, normalized to a Quality enum value
    """

    crate: Optional[str] = ''  # XXX (zkanzler): what is this field *supposed* to describe?
    """
    If defined, the name of the crate the item originated from

    NOTE: this field is None for all items in my personal inventory
    """

    amount: int = 1
    """
    Always 1
    """

    instance_id: int = 0
    """
    Always 0

    Ref: https://github.com/Bakkes/BetterInventoryExport/blob/214fbafc0dd58126d1374809c6b62a18dc74b32f/README.md?plain=1#L12-L13
    Ref: https://github.com/Bakkes/BetterInventoryExport/blob/214fbafc0dd58126d1374809c6b62a18dc74b32f/BetterInventoryExport/BetterInventoryExport.cpp#L170
    """

    special_edition: Optional[SpecialEdition] = None
    """
    Special edition, which signifies item alterations such as Inverted, Holographic, or Infinite.
    """

    blueprint_item_id: Optional[int] = None
    """
    If item is a blueprint, this is the ID of the item the blueprint unlocks
    """

    blueprint_item: Optional[str] = None
    """
    If item is a blueprint, this is the name of the item the blueprint unlocks
    """

    blueprint_cost: Optional[int] = None
    """
    If item is a blueprint, this is the number of credits needed to unlock the blueprint
    """

    tradeable: bool = False
    """
    Whether the item can be traded with other players
    """

    # TODO (zkanzler): it would be nice if there was a "trade-in-able" attr

    @classmethod
    def from_raw_item(cls: Type[InventoryItem_t], item: RawInventoryItem) -> InventoryItem_t:
        attrs = dict(item)

        for name, transform in RAW_ITEM_TRANSFORMS.items():
            if name in attrs:
                attrs[name] = transform(attrs[name])

        return cls(**attrs)  # type: ignore[arg-type]

    def __init__(
        self,
        product_id: int,
        name: str,
        slot: Slot | str,
        paint: Optional[Paint | str],
        certification: Optional[Certification | str],
        certification_value: int,
        rank_label: Optional[str],
        quality: Quality | str,
        crate: Optional[str],
        amount: int,
        instance_id: int,
        special_edition: Optional[str | SpecialEdition],
        blueprint_item_id: Optional[int],
        blueprint_item: Optional[str],
        blueprint_cost: Optional[int],
        tradeable: bool,
    ):
        if isinstance(slot, str):
            slot = Slot(slot)
        if isinstance(paint, str):
            paint = Paint(paint)
        if isinstance(certification, str):
            certification_type = CertificationType(certification)
            certification = Certification(certification_type, certification_value)
        if isinstance(quality, str):
            quality = Quality(quality)
        if isinstance(special_edition, str):
            special_edition = SpecialEdition(special_edition)

        self.product_id = product_id
        self.name = name
        self.slot = slot
        self.paint = paint
        self.certification = certification
        self.certification_value = certification_value
        self.rank_label = rank_label
        self.quality = quality
        self.crate = crate
        self.amount = amount
        self.instance_id = instance_id
        self.special_edition = special_edition
        self.blueprint_item_id = blueprint_item_id
        self.blueprint_item = blueprint_item
        self.blueprint_cost = blueprint_cost
        self.tradeable = tradeable

    @property
    def is_blueprint(self) -> bool:
        return self.blueprint_item is not None

    @property
    def is_certified(self) -> bool:
        return self.certification is not None

    @property
    def is_tradeable(self):
        # Alias, to match `is_xyz` convention
        return self.tradeable

    @property
    def item_id(self) -> int:
        """ID of item, or item the blueprint would produce"""
        return self.blueprint_item_id or self.product_id

    @property
    def item_name(self) -> str:
        """Name of item, or item the blueprint would produce"""
        return self.blueprint_item or self.name

    def __str__(self) -> str:
        components = [
            f'{self.slot}:',
            self.item_name,
            f'[{self.quality.pretty}]',
        ]

        components.extend(
            f'[{getattr(tag, "pretty", tag)}]'
            for tag in (self.paint, self.special_edition)
            if tag
        )

        if self.certification:
            components.append(f'[{self.certification.full_str()}]')

        return ' '.join(components)


def transform_raw_optional_str(s: str) -> Optional[str]:
    return None if s == 'none' else s


def transform_raw_bool(s: str) -> bool:
    return True if s == 'true' else False


def none_if_zero(n: int) -> Optional[int]:
    return n or None


def none_if_empty(s: str) -> Optional[str]:
    return s or None


RAW_ITEM_TRANSFORMS: dict[str, Callable[[Any], Any]] = {
    'paint': transform_raw_optional_str,
    'certification': transform_raw_optional_str,
    'rank_label': transform_raw_optional_str,
    'crate': none_if_empty,
    'special_edition': transform_raw_optional_str,
    'blueprint_item_id': none_if_zero,
    'blueprint_item': none_if_empty,
    'blueprint_cost': none_if_zero,
    'tradeable': transform_raw_bool,
}

CERTIFICATION_TAGS: dict[CertificationType, str] = {
    CertificationType.SHOTS_ON_GOAL: 'Striker',
    CertificationType.CLEARS: 'Sweeper',
    CertificationType.CENTERS: 'Tactician',
    CertificationType.BICYCLE_GOALS: 'Acrobat',
    CertificationType.AERIAL_GOALS: 'Aviator',
    CertificationType.SAVES: 'Goalkeeper',
    CertificationType.EPIC_SAVES: 'Guardian',
    CertificationType.JUGGLES: 'Juggler',
    CertificationType.ASSISTS: 'Playmaker',
    CertificationType.GOALS: 'Scorer',
    CertificationType.BACKWARDS_GOALS: 'Show-Off',
    CertificationType.LONG_GOALS: 'Sniper',
    CertificationType.TURTLE_GOALS: 'Turtle',
    CertificationType.MVPS: 'Paragon',
    CertificationType.WINS: 'Victor',
}

_LEVELS_STRIKER_TO_TACTICIAN = (0, 50, 100, 200, 500, 1_000, 2_000, 5_000, 10_000, 18_000)
_LEVELS_ACROBAT_TO_TURTLE = (0, 25, 50, 100, 250, 500, 1_000, 2_500, 5_000, 9_000)
_LEVELS_PARAGON_VICTOR = (0, 10, 25, 50, 125, 250, 500, 1_250, 2_500, 4_500)

CERTIFICATION_LEVELS: dict[
    CertificationType, tuple[int, int, int, int, int, int, int, int, int, int]  # 10 levels each
] = {
    CertificationType.SHOTS_ON_GOAL: _LEVELS_STRIKER_TO_TACTICIAN,
    CertificationType.CLEARS: _LEVELS_STRIKER_TO_TACTICIAN,
    CertificationType.CENTERS: _LEVELS_STRIKER_TO_TACTICIAN,
    CertificationType.BICYCLE_GOALS: _LEVELS_ACROBAT_TO_TURTLE,
    CertificationType.AERIAL_GOALS: _LEVELS_ACROBAT_TO_TURTLE,
    CertificationType.SAVES: _LEVELS_ACROBAT_TO_TURTLE,
    CertificationType.EPIC_SAVES: _LEVELS_ACROBAT_TO_TURTLE,
    CertificationType.JUGGLES: _LEVELS_ACROBAT_TO_TURTLE,
    CertificationType.ASSISTS: _LEVELS_ACROBAT_TO_TURTLE,
    CertificationType.GOALS: _LEVELS_ACROBAT_TO_TURTLE,
    CertificationType.BACKWARDS_GOALS: _LEVELS_ACROBAT_TO_TURTLE,
    CertificationType.LONG_GOALS: _LEVELS_ACROBAT_TO_TURTLE,
    CertificationType.TURTLE_GOALS: _LEVELS_ACROBAT_TO_TURTLE,
    CertificationType.MVPS: _LEVELS_PARAGON_VICTOR,
    CertificationType.WINS: _LEVELS_PARAGON_VICTOR,
}


_LEVEL_NAMES_1_TO_5 = (
    'Certified',
    'Capable',
    'Skillful',
    'Veteran',
    'Fantastic',
)

CERTIFICATION_LEVEL_NAMES: dict[
    CertificationType, tuple[str, str, str, str, str, str, str, str, str, str]  # 10 levels each
] = {
    CertificationType.SHOTS_ON_GOAL: (
        *_LEVEL_NAMES_1_TO_5,
        'Incredible',
        'Absurd',
        'Unreal',
        'Unrelenting',
        'Berserker',
    ),
    CertificationType.CLEARS: (
        *_LEVEL_NAMES_1_TO_5,
        'Ridiculous',
        'Unbelievable',
        'Preposterous',
        'Stupendous',
        'Chief Custodian',
    ),
    CertificationType.CENTERS: (
        *_LEVEL_NAMES_1_TO_5,
        'Ridiculous',
        'Unbelievable',
        'Preposterous',
        'Tremendous',
        'Master Planner',
    ),
    CertificationType.BICYCLE_GOALS: (
        *_LEVEL_NAMES_1_TO_5,
        'Ridiculous',
        'Unbelievable',
        'Preposterous',
        'Astounding',
        'Cyclist',
    ),
    CertificationType.AERIAL_GOALS: (
        *_LEVEL_NAMES_1_TO_5,
        'Ridiculous',
        'Unbelievable',
        'Preposterous',
        'Impenetrable',
        'Immovable Object',
    ),
    CertificationType.SAVES: (
        *_LEVEL_NAMES_1_TO_5,
        'Ridiculous',
        'Unbelievable',
        'Preposterous',
        'Impenetrable',
        'Immovable Object',
    ),
    CertificationType.EPIC_SAVES: (
        *_LEVEL_NAMES_1_TO_5,
        'Ridiculous',
        'Unbelievable',
        'Preposterous',
        'Gallant',
        'Guardian Angel',
    ),
    CertificationType.JUGGLES: (
        *_LEVEL_NAMES_1_TO_5,
        'Incredible',
        'Absurd',
        'Unreal',
        'Marvelous',
        'Magician',
    ),
    CertificationType.ASSISTS: (
        *_LEVEL_NAMES_1_TO_5,
        'Incredible',
        'Absurd',
        'Unreal',
        'Psychic',
        'Unsung Hero',
    ),
    CertificationType.GOALS: (
        *_LEVEL_NAMES_1_TO_5,
        'Incredible',
        'Absurd',
        'Unreal',
        'Supersonic',
        'Unstoppable Force',
    ),
    CertificationType.BACKWARDS_GOALS: (
        *_LEVEL_NAMES_1_TO_5,
        'Daring',
        'Relentless',
        'Exhausting',
        'Cheeky',
        'Total Showboat',
    ),
    CertificationType.LONG_GOALS: (
        *_LEVEL_NAMES_1_TO_5,
        'Incredible',
        'Absurd',
        'Unreal',
        'Unforgiving',
        'Cold-Blooded',
    ),
    CertificationType.TURTLE_GOALS: (
        *_LEVEL_NAMES_1_TO_5,
        'Ridiculous',
        'Unbelievable',
        'Reckless',
        'Timeless',
        'Turtle God',
    ),
    CertificationType.MVPS: (
        *_LEVEL_NAMES_1_TO_5,
        'Determined',
        'Stunning',
        'Wonderful',
        'Eternal',
        'The Most Valuable',
    ),
    CertificationType.WINS: (
        *_LEVEL_NAMES_1_TO_5,
        'Daring',
        'Relentless',
        'Fearless',
        'Valiant',
        'Unbeatable',
    ),
}
