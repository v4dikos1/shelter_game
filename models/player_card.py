from dataclasses import dataclass, field
from typing import Dict, List

from models.scenario import Item, SpecialCard


@dataclass
class PlayerCard:
    characteristics: Dict[str, str]
    items: List[Item] = field(default_factory=list)
    special_cards: List[SpecialCard] = field(default_factory=list)
    revealed_values: List[str] = field(default_factory=list)

    def to_dict(self):
        return {"characteristics": self.characteristics,
                "items":[i.to_dict() for i in self.items],
                "special_cards": [c.to_dict() for c in self.special_cards],
                "revealed_values": self.revealed_values}

    @staticmethod
    def from_dict(data):
        return PlayerCard(characteristics=data["characteristics"],
                          items=[Item.from_dict(i) for i in data["items"]],
                          special_cards=[SpecialCard.from_dict(c) for c in data["special_cards"]],
                          revealed_values=data["revealed_values"])
