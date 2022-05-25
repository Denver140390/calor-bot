from dataclasses import dataclass
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional
import commands
from Items import FoodItem, EatenItem


class Service:
    START_DATE_OFFSET_HOURS = 3

    def __init__(self):
        # TODO store by user id
        self.weights: List[Decimal] = []
        self.food_items: List[FoodItem] = []
        self.eaten_items: List[EatenItem] = []

    @staticmethod
    def now() -> datetime:
        return datetime.now()  # TODO client timezone

    @staticmethod
    def today() -> date:
        return date.today()  # TODO client timezone

    def get_weights_desc(self) -> tuple[Decimal]:
        return tuple(self.weights)

    def add_weight(self, command: commands.AddWeightCommand) -> List[str]:
        self.weights.append(command.weight)
        response = f'Your current weight is {command.weight} kg. Got it!'
        if len(self.weights) == 1:
            return [response]
        else:
            return [f'{response} Yesterday it was {self.weights[-2]} kg.']

    def add_food_item(self, food_item_name: str, calories_per_100_grams: Decimal) -> FoodItem:
        food_item = FoodItem(food_item_name, calories_per_100_grams=calories_per_100_grams, added_on=self.now())
        self.food_items.append(food_item)
        return food_item

    def add_weighted_eaten_item(self, item: FoodItem, weight_grams: Decimal) -> None:
        responses: List[str] = []
        now = self.now()
        # item_candidates = self.search_food_item(command.item_name)

        # if not item_candidates:
        #     item = FoodItem(
        #         name=command.item_name,
        #         calories_per_100_grams=command.calories_per_100_grams,
        #         added_on=self.now())
        #     self.food_items.append(item)
        #     responses.append(
        #         f'Could not find existing food entry by name {command.item_name}. Created a new one: {item}.')
        #
        # elif len(item_candidates) > 1:
        #     # TODO suggest choosing from them
        #     responses.append(f'Multiple entries match {command.item_name}. Please, enter a more specific food name.')
        #     return responses
        #
        # else:  # exactly one item found TODO compare by other fields, should be equal
        #     item = item_candidates[0]
        #     responses.append(f'Found existing food entry: {item}, counting on that.')

        eaten_item = EatenItem(item, weight_grams=weight_grams, added_on=now)
        self.eaten_items.append(eaten_item)

    def add_total_calories_eaten_item(self, command: commands.AddTotalCaloriesEatenItemCommand) -> List[str]:
        pass

    def get_today_eaten_calories(self) -> Decimal:
        # Calculate eaten calories from 3 AM to 3 AM just in case of late dinner
        today = (self.now() - timedelta(hours=self.START_DATE_OFFSET_HOURS)).date()
        today_start_datetime = datetime(today.year, today.month, today.day, self.START_DATE_OFFSET_HOURS)
        today_eaten_calories = [item.calories_eaten for item in self.eaten_items if item.added_on > today_start_datetime]
        today_eaten_calories_sum = sum(today_eaten_calories)
        return today_eaten_calories_sum

    def search_food_item(self, item_name) -> Optional[List[FoodItem]]:
        candidates = [item for item in self.food_items if item_name in item.name]
        return candidates
