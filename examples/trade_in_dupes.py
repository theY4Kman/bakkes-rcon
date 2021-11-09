"""
This script emits groups of 5 same-quality duplicate items that may be traded in safely,
without losing possession of items of the same product and same colour.
"""
import asyncio
from collections import defaultdict
from itertools import islice
from typing import cast, Dict, List, Tuple

from bakkes_rcon import BakkesRconClient, InventoryItem, Quality


ToplevelKey = Tuple[bool, Quality]
ItemKey = Tuple[int, str, str]
TradeInGroup = Tuple[InventoryItem, InventoryItem, InventoryItem, InventoryItem, InventoryItem]


def window(seq, n=2):
    """Returns a sliding window (of width n) over data from the iterable"""
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result


# Maps the item quality to the Trade In menu item that should be clicked to trade the items in
trade_in_quality_menu_map = {
    item_quality: menu_item_quality
    for item_quality, menu_item_quality in window(Quality, n=2)
    if item_quality < Quality.BLACK_MARKET
}


async def main():
    async with BakkesRconClient() as client:
        inventory = await client.get_inventory()
        tradeable = [item for item in inventory if item.is_tradeable]

        toplevel_buckets: Dict[ToplevelKey, Dict[ItemKey, List[InventoryItem]]] = (
            defaultdict(lambda: defaultdict(list))
        )
        for item in tradeable:
            if item.quality in (Quality.BLACK_MARKET, Quality.LIMITED):
                # Cannot trade in Black Market or Limited items
                continue

            toplevel_key = (item.is_blueprint, item.quality)
            toplevel_bucket = toplevel_buckets[toplevel_key]

            item_key = (item.item_id, item.paint, item.special_edition)
            toplevel_bucket[item_key].append(item)

        groups: List[TradeInGroup] = []
        for toplevel_bucket in toplevel_buckets.values():
            buf: List[InventoryItem] = []

            item_buckets = list(toplevel_bucket.values())
            item_buckets.sort(key=lambda item_bucket: item_bucket[0].item_name)

            for item_bucket in item_buckets:
                if len(item_bucket) < 2:
                    continue

                item_bucket.sort(key=lambda item: item.is_certified)
                buf += item_bucket[1:]

                while len(buf) >= 5:
                    group = tuple(sorted(buf[:5], key=lambda item: item.item_name))
                    groups.append(cast(TradeInGroup, group))
                    buf = buf[5:]

        if not groups:
            print('No suitable trade-in groups found')
            return

        # Show blueprint items last, and sort by quality, ascending
        groups.sort(key=lambda group: (group[0].is_blueprint, group[0].quality))

        for buf in groups:
            first_item = buf[0]

            if first_item.is_blueprint:
                print('Blueprint: ', end='')
            print(first_item.quality, '=>', trade_in_quality_menu_map[first_item.quality])

            for item in buf:
                print(f'  {item}')

            print()
            print()


if __name__ == '__main__':
    asyncio.run(main())
