from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class FoodItem:
    name: str
    calories_per_100_grams: Decimal
    added_on: datetime

    def __str__(self) -> str:
        return f'{self.name}, {self.calories_per_100_grams or "UNKNOWN"} cal per 100 grams'


@dataclass
class EatenItem:
    item: FoodItem
    weight_grams: Decimal
    added_on: datetime

    @property
    def calories_eaten(self) -> Decimal:
        return self.item.calories_per_100_grams / 100 * self.weight_grams

    def __str__(self) -> str:
        return f'{self.item}, {self.weight_grams} grams, a total of {self.calories_eaten} cal'
