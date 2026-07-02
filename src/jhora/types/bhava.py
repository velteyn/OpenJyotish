from enum import IntEnum


class Bhava(IntEnum):
    BHAVA_1 = 1
    BHAVA_2 = 2
    BHAVA_3 = 3
    BHAVA_4 = 4
    BHAVA_5 = 5
    BHAVA_6 = 6
    BHAVA_7 = 7
    BHAVA_8 = 8
    BHAVA_9 = 9
    BHAVA_10 = 10
    BHAVA_11 = 11
    BHAVA_12 = 12

    @property
    def is_kendra(self) -> bool:
        return self.value in (1, 4, 7, 10)

    @property
    def is_konas(self) -> bool:
        return self.value in (1, 5, 9)

    @property
    def is_trikona(self) -> bool:
        return self.value in (1, 5, 9)

    @property
    def is_upachaya(self) -> bool:
        return self.value in (3, 6, 10, 11)

    @property
    def is_apoklima(self) -> bool:
        return self.value in (3, 6, 9, 12)

    @property
    def is_duhsthana(self) -> bool:
        return self.value in (6, 8, 12)

    @property
    def is_trik(self) -> bool:
        return self.value in (6, 8, 12)

    @property
    def is_maraka(self) -> bool:
        return self.value in (2, 7)

    @property
    def meaning(self) -> str:
        return _BHAVA_MEANINGS[self]


_BHAVA_MEANINGS = {
    Bhava.BHAVA_1: "Self, body, personality",
    Bhava.BHAVA_2: "Wealth, family, speech",
    Bhava.BHAVA_3: "Courage, siblings, communication",
    Bhava.BHAVA_4: "Home, mother, happiness",
    Bhava.BHAVA_5: "Children, intelligence, mantra",
    Bhava.BHAVA_6: "Enemies, disease, debts",
    Bhava.BHAVA_7: "Spouse, business, marriage",
    Bhava.BHAVA_8: "Longevity, occult, obstacles",
    Bhava.BHAVA_9: "Fortune, dharma, guru",
    Bhava.BHAVA_10: "Career, status, karma",
    Bhava.BHAVA_11: "Gains, fulfillment, income",
    Bhava.BHAVA_12: "Loss, expenditure, moksha",
}
