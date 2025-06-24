from enum import StrEnum
from typing import Literal


class Poignee(StrEnum):
    SIMPLE = "1️⃣"
    DOUBLE = "2️⃣"
    TRIPLE = "3️⃣"

    @property
    def score(self) -> int:
        match self:
            case Poignee.SIMPLE:
                return 20
            case Poignee.DOUBLE:
                return 30
            case Poignee.TRIPLE:
                return 40


class Attack(StrEnum):
    PETITE = "🤏"
    GUARDE = "🐶"
    GUARDE_SANS = "💂"
    GUARDE_CONTRE = "🥷"

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


class PetitAuBout(StrEnum):
    ATTACK = "⚔️"
    DEFENSE = "🛡️"

    @property
    def score(self) -> int:
        match self:
            case PetitAuBout.ATTACK:
                return 10
            case PetitAuBout.DEFENSE:
                return -10
