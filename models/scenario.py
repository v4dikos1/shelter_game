from typing import List, Tuple, Dict
from dataclasses import dataclass, field

@dataclass
class WinCondition:
    type: str
    value: int

    def to_dict(self):
        return {"type": self.type, "value": self.value}

    @staticmethod
    def from_dict(data):
        return WinCondition(type=data["type"], value=data["value"])

@dataclass
class Action:
    type: str
    dice_range: Tuple[int, int] = None

    def to_dict(self):
        return {"type": self.type, "dice_range": self.dice_range}

    @staticmethod
    def from_dict(data):
        return Action(type=data["type"], dice_range=data["dice_range"])

@dataclass
class Item:
    name: str
    description: str
    actions: List[Action] = field(default_factory=list)

    def to_dict(self):
        return {"name": self.name, "description": self.description, "actions": [a.to_dict() for a in self.actions] }

    @staticmethod
    def from_dict(data):
        return Item(name=data["name"], description=data["description"], actions=[Action.from_dict(a) for a in data["actions"]])

@dataclass
class BunkerFeature:
    name: str
    description: str

    def to_dict(self):
        return {"name": self.name,
                "description": self.description}

    @staticmethod
    def from_dict(data):
        return BunkerFeature(name=data["name"],
                      description=data["description"])


@dataclass
class SpecialCardAction:
    type: str

    def to_dict(self):
        return {"type": self.type}

    @staticmethod
    def from_dict(data):
        return SpecialCardAction(type=data["type"])

@dataclass
class SpecialCard:
    name: str
    description: str
    actions: List[SpecialCardAction]= field(default_factory=list)

    def to_dict(self):
        return {"name": self.name, "description": self.description, "actions": [a.to_dict() for a in self.actions] }

    @staticmethod
    def from_dict(data):
        return SpecialCard(name=data["name"], description=data["description"], actions=[SpecialCardAction.from_dict(a) for a in data["actions"]])

@dataclass
class BaseAction:
    id: str
    name: str
    description: str

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description}

    @staticmethod
    def from_dict(data):
        return BaseAction(id=data["id"], name=data["name"], description=data["description"])

@dataclass
class Scenario:
    id: str
    name: str
    description: str
    win_condition: WinCondition
    characteristics: Dict[str, List[str]]
    items: List[Item] = field(default_factory=list)
    bunker_features: List[BunkerFeature] = field(default_factory=list)
    special_cards: List[SpecialCard] = field(default_factory=list)
    base_actions: List[BaseAction] = field(default_factory=list)