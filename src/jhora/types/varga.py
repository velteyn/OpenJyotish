from enum import IntEnum, auto
from typing import Dict, List, Tuple


class VargaLevel(IntEnum):
    D_1 = 1
    D_2 = 2
    D_3 = 3
    D_4 = 4
    D_5 = 5
    D_6 = 6
    D_7 = 7
    D_8 = 8
    D_9 = 9
    D_10 = 10
    D_11 = 11
    D_12 = 12
    D_16 = 16
    D_20 = 20
    D_24 = 24
    D_27 = 27
    D_30 = 30
    D_40 = 40
    D_45 = 45
    D_60 = 60
    D_81 = 81
    D_108 = 108
    D_144 = 144
    D_150 = 150

    @property
    def divisions(self) -> int:
        return self.value

    @property
    def short_name(self) -> str:
        return f"D-{self.value}"

    @property
    def full_name(self) -> str:
        return _VARGA_NAMES.get(self, f"D-{self.value}")

    @property
    def bhava_supported(self) -> bool:
        return self in _BHAVA_SUPPORTED


_VARGA_NAMES = {
    VargaLevel.D_1: "Rasi",
    VargaLevel.D_2: "Hora",
    VargaLevel.D_3: "Drekkana",
    VargaLevel.D_4: "Chaturthamsa",
    VargaLevel.D_5: "Panchamsa",
    VargaLevel.D_7: "Saptamsa",
    VargaLevel.D_8: "Ashtamsa",
    VargaLevel.D_9: "Navamsa",
    VargaLevel.D_10: "Dasamsa",
    VargaLevel.D_11: "Rudramsa",
    VargaLevel.D_12: "Dwadasamsa",
    VargaLevel.D_16: "Shodashamsa",
    VargaLevel.D_20: "Vimsamsa",
    VargaLevel.D_24: "Chaturvimsamsa",
    VargaLevel.D_27: "Saptavimsamsa",
    VargaLevel.D_30: "Trimamsa",
    VargaLevel.D_40: "Khavedamsa",
    VargaLevel.D_45: "Akshavedamsa",
    VargaLevel.D_60: "Shashtiamsa",
    VargaLevel.D_81: "Nava-nava",
    VargaLevel.D_108: "Ashta-uttara",
    VargaLevel.D_144: "Dwadasha-dwadasha",
    VargaLevel.D_150: "Prajnapada",
}

_BHAVA_SUPPORTED = {
    VargaLevel.D_1, VargaLevel.D_2, VargaLevel.D_3, VargaLevel.D_4,
    VargaLevel.D_5, VargaLevel.D_6, VargaLevel.D_7, VargaLevel.D_8,
    VargaLevel.D_9, VargaLevel.D_10, VargaLevel.D_11, VargaLevel.D_12,
    VargaLevel.D_16, VargaLevel.D_20, VargaLevel.D_24, VargaLevel.D_27,
    VargaLevel.D_30, VargaLevel.D_40, VargaLevel.D_45, VargaLevel.D_60,
    VargaLevel.D_81, VargaLevel.D_108, VargaLevel.D_144,
}


class VargaVariant(IntEnum):
    DEFAULT = 0
    TRD = auto()
    REV = auto()
    REV2 = auto()
    PV = auto()
    B = auto()
    K = auto()
    KM = auto()
    UKM = auto()
    JN = auto()
    SN = auto()
    US = auto()
    RA = auto()
    RM = auto()
    RMM = auto()
    NI = auto()
    NIM = auto()
    MD = auto()
    LM = auto()
    CNL = auto()
    SN2 = auto()
    KN = auto()
    AR = auto()
    RVAR = auto()
    SH = auto()
    V1_7 = auto()
    V7_1 = auto()
    V5_8 = auto()
    V6_9 = auto()
    V9_12 = auto()
    K_N_RAO = auto()
