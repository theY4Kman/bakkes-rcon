from typing import Literal, TypeAlias, TypedDict

RawOptionalStr: TypeAlias = str | Literal['none']
RawBool: TypeAlias = Literal['true', 'false']


class RawInventoryItem(TypedDict):
    product_id: int
    name: str
    slot: str
    paint: RawOptionalStr
    certification: RawOptionalStr
    certification_value: int
    rank_label: RawOptionalStr
    quality: str
    crate: str
    amount: int  # seems to only ever be 1
    instance_id: int
    special_edition: RawOptionalStr
    blueprint_item_id: int
    blueprint_item: str
    blueprint_cost: int
    tradeable: RawBool
