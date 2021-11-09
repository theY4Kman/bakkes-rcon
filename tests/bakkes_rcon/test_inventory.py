from bakkes_rcon.inventory import Quality


class DescribeQuality:
    def it_sorts_according_to_better_inventory_export(self):
        """
        Ordering should match BetterInventoryExport's ProductQuality enum ordering

        Ref: https://github.com/Bakkes/BetterInventoryExport/blob/214fbafc0dd58126d1374809c6b62a18dc74b32f/BetterInventoryExport/BetterInventoryExport.h#L8-L21
        """
        expected = [
            Quality.COMMON,
            Quality.UNCOMMON,
            Quality.RARE,
            Quality.VERY_RARE,
            Quality.IMPORT,
            Quality.EXOTIC,
            Quality.BLACK_MARKET,
            Quality.PREMIUM,
            Quality.LIMITED,
            Quality.LEGACY,
        ]
        actual = sorted(reversed(expected))
        assert expected == actual

    def its_int_values_match_better_inventory_export(self):
        """
        The integer values of each enum item should match BetterInventoryExport's
        ProductQuality enum values

        Ref: https://github.com/Bakkes/BetterInventoryExport/blob/214fbafc0dd58126d1374809c6b62a18dc74b32f/BetterInventoryExport/BetterInventoryExport.h#L8-L21
        """
        expected = {
            Quality.COMMON: 0,
            Quality.UNCOMMON: 1,
            Quality.RARE: 2,
            Quality.VERY_RARE: 3,
            Quality.IMPORT: 4,
            Quality.EXOTIC: 5,
            Quality.BLACK_MARKET: 6,
            Quality.PREMIUM: 7,
            Quality.LIMITED: 8,
            Quality.LEGACY: 9,
        }
        actual = {quality: int(quality) for quality in expected}
        assert expected == actual
