from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional
import commands
from repository import Repository
from items import FoodItem, EatenItem, Weight


class Service:
    START_DATE_OFFSET_HOURS = 3

    @staticmethod
    def now() -> datetime:
        return datetime.now()  # TODO client timezone

    @staticmethod
    def today() -> date:
        return date.today()  # TODO client timezone

    def add_weight(self, weight_kilograms: Decimal) -> List[str]:
        weight = Weight(weight_kilograms, self.now())
        Repository().add_weight(weight)
        weights = Repository().get_weights_desc()
        response = f'Your current weight is {weight.weight_kilograms} kg. Got it!'
        if len(weights) == 1:
            return [response]
        else:
            # TODO can be multiple entries per day, gotta select first per yesterday
            return [f'{response} Yesterday it was {weights[-2].weight_kilograms} kg.']

    def add_food_item(self, name: str, calories_per_100_grams: Decimal) -> FoodItem:
        food_item = Repository().add_food_item(name, calories_per_100_grams, self.now())
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
        Repository().add_eaten_item(eaten_item)

    def add_total_calories_eaten_item(self, command: commands.AddTotalCaloriesEatenItemCommand) -> List[str]:
        pass

    def get_today_eaten_calories(self) -> Decimal:
        # Calculate eaten calories from 3 AM to 3 AM just in case of late dinner
        today = (self.now() - timedelta(hours=self.START_DATE_OFFSET_HOURS)).date()
        today_start_datetime = datetime(today.year, today.month, today.day, self.START_DATE_OFFSET_HOURS)
        eaten_items = Repository().get_eaten_items()
        today_eaten_calories = [item.calories_eaten for item in eaten_items if item.added_on > today_start_datetime]
        today_eaten_calories_sum = sum(today_eaten_calories)
        return today_eaten_calories_sum

    @staticmethod
    def search_food_item(item_name) -> Optional[List[FoodItem]]:
        food_items = Repository().get_food_items()
        candidates = [item for item in food_items if item_name in item.name]
        return candidates
