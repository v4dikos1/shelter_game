import json
from typing import List
from models.scenario import Scenario, WinCondition, Item, Action, BunkerFeature, SpecialCard, SpecialCardAction, \
    BaseAction


def load_scenarios_from_file(path: str) -> List[Scenario]:
    with open(path, encoding='utf-8') as f:
        raw_data = json.load(f)

    scenarios = []
    for s in raw_data:
        win_condition = WinCondition.from_dict(s["win_condition"])

        items = [
            Item.from_dict(i)
            for i in s.get("items", [])
        ]

        bunker_features = [BunkerFeature.from_dict(bf) for bf in s.get("bunker_features", [])]

        special_cards = [
            SpecialCard.from_dict(sc)
            for sc in s.get("special_cards", [])
        ]

        base_actions = [BaseAction.from_dict(a) for a in s.get("base_actions", [])]

        scenario = Scenario(
            id=s["id"],
            name=s["name"],
            description=s["description"],
            win_condition=win_condition,
            characteristics=s["characteristics"],
            items=items,
            bunker_features=bunker_features,
            special_cards=special_cards,
            base_actions=base_actions
        )

        scenarios.append(scenario)

    return scenarios


SCENARIOS = load_scenarios_from_file("D:\\Bunker\\utils\\config.json")
