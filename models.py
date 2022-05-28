from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Weight:
    weight_kilograms: Decimal
    added_on: datetime


@dataclass(frozen=True)
class FoodComposition:
    pass


@dataclass(frozen=True)
class Food:
    id: int
    name: str
    calories_per_100_grams: Decimal
    # composition: Optional[FoodComposition]
    added_on: datetime

    def __str__(self) -> str:
        return f'{self.name}, {self.calories_per_100_grams or "UNKNOWN"} cal per 100 grams'


@dataclass(frozen=True)
class EatenFood:
    food: Food
    weight_grams: Decimal
    added_on: datetime

    @property
    def calories_eaten(self) -> Decimal:
        return self.food.calories_per_100_grams / 100 * self.weight_grams

    def __str__(self) -> str:
        return f'{self.food}, {self.weight_grams} grams, a total of {self.calories_eaten} cal'
