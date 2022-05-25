from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Command:
    pass


@dataclass
class AddWeightCommand(Command):
    weight: Decimal


@dataclass
class AddWeightedEatenItemCommand(Command):
    item_name: str
    calories_per_100_grams: Decimal
    weight_grams: Decimal


@dataclass
class AddTotalCaloriesEatenItemCommand(Command):
    dish_name: str
    total_calories: Decimal
