from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Tuple


@dataclass(frozen=True)
class Weight:
    weight_kilograms: Decimal
    added_on: datetime


@dataclass(frozen=True)
class FoodIngredient:
    pass


@dataclass(frozen=True)
class Food(ABC):
    id: int
    name: str
    added_on: datetime

    @abstractmethod
    def __str__(self) -> str:
        pass


@dataclass(frozen=True)
class WeightedFood(Food):
    calories_per_100_grams: Decimal

    def __str__(self) -> str:
        return f'{self.name}, {self.calories_per_100_grams} cal per 100 grams'


@dataclass(frozen=True)
class CompositionFood(Food):
    ingredients: Tuple[FoodIngredient]
    calories_per_100_grams: Decimal

    def __str__(self) -> str:
        return f'{self.name}, {self.calories_per_100_grams} cal per 100 grams'


@dataclass(frozen=True)
class PortionFood(Food):
    portion_calories: Decimal

    def __str__(self) -> str:
        return f'{self.name}, {self.portion_calories} cal total'


@dataclass(frozen=True)
class EatenFood(ABC):
    food: Food
    added_on: datetime

    @abstractmethod
    def eaten_calories(self) -> Decimal:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


@dataclass(frozen=True)
class EatenWeightedFood(EatenFood):
    food: WeightedFood
    weight_grams: Decimal

    def eaten_calories(self) -> Decimal:
        return self.food.calories_per_100_grams / 100 * self.weight_grams

    def __str__(self) -> str:
        return f'{self.food}, {self.weight_grams} grams, a total of {self.eaten_calories} cal'


@dataclass(frozen=True)
class EatenCompositionFood(EatenFood):
    food: CompositionFood
    weight_grams: Decimal

    def eaten_calories(self) -> Decimal:
        return self.food.calories_per_100_grams / 100 * self.weight_grams

    def __str__(self) -> str:
        return f'{self.food}, {self.weight_grams} grams, a total of {self.eaten_calories} cal'


@dataclass(frozen=True)
class EatenPortionFood(EatenFood):
    food: PortionFood

    def eaten_calories(self) -> Decimal:
        return self.food.portion_calories

    def __str__(self) -> str:
        return f'{self.food}'
