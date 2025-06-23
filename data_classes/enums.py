from enum import Enum


class Poignee(str, Enum):
    NONE = "Non"
    SIMPLE = "1️⃣ Simple"
    DOUBLE = "2️⃣ Double"
    TRIPLE = "3️⃣ Triple"

    @property
    def score(self) -> int:
        match self:
            case Poignee.NONE:
                return 0
            case Poignee.SIMPLE:
                return 20
            case Poignee.DOUBLE:
                return 30
            case Poignee.TRIPLE:
                return 40


class Attack(str, Enum):
    PETITE = "🤏 Petite"
    GUARDE = "🐶 Guard"
    GUARDE_SANS = "💂 Guarde sans"
    GUARDE_CONTRE = "🥷 Guarde contre"

    @property
    def multiplicator(self) -> int:
        match self:
            case Attack.PETITE:
                return 1
            case Attack.GUARDE:
                return 2
            case Attack.GUARDE_SANS:
                return 4
            case Attack.GUARDE_CONTRE:
                return 6
