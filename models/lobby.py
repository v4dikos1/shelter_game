from typing import List
from dataclasses import dataclass, field

from models.player_card import PlayerCard
from models.scenario import BunkerFeature


@dataclass
class Player:
    user_id: int
    username: str
    cards: PlayerCard | None

    def to_dict(self):
        return {"user_id": self.user_id,
                "username": self.username,
                "cards": self.cards.to_dict() if self.cards else None}

    @staticmethod
    def from_dict(data):
        return Player(user_id=data["user_id"],
                      username=data["username"],
                      cards=PlayerCard.from_dict(data["cards"]) if data["cards"] else None)

@dataclass
class Bunker:
    scenario_id: str
    scenario_name: str
    scenario_description: str
    features: List[BunkerFeature] = field(default_factory=list)

    def to_dict(self):
        return {"scenario_id": self.scenario_id,
                "scenario_name": self.scenario_name,
                "scenario_description": self.scenario_description,
                "features": [f.to_dict() for f in self.features]}

    @staticmethod
    def from_dict(data):
        return Bunker(scenario_id=data["scenario_id"],
                      scenario_name=data["scenario_name"],
                      scenario_description=data["scenario_description"],
                      features=[BunkerFeature.from_dict(f) for f in data["features"]])

@dataclass
class Lobby:
    code: str
    owner: Player
    bunker: Bunker | None
    players: List[Player] = field(default_factory=list)
    started: bool = False


    def to_dict(self):
        return {
            "code": self.code,
            "owner": self.owner.to_dict(),
            "players": [p.to_dict() for p in self.players],
            "started": self.started,
            "bunker": self.bunker.to_dict() if self.bunker else None
        }

    @staticmethod
    def from_dict(data):
        return Lobby(
            code=data["code"],
            owner=Player.from_dict(data["owner"]),
            players=[Player.from_dict(p) for p in data["players"]],
            started=data.get("started", False),
            bunker=Bunker.from_dict(data["bunker"]) if data["bunker"] else None,
        )
