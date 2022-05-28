from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional
from repository import Repository
from models import Weight, WeightedFood, EatenWeightedFood, Food, PortionFood, EatenPortionFood


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

    def add_weighted_food(self, food_name: str, calories_per_100_grams: Decimal) -> WeightedFood:
        return Repository().add_weighted_food(food_name, calories_per_100_grams, self.now())

    def add_portion_food(self, food_name: str, calories_per_portion: Decimal) -> PortionFood:
        return Repository().add_portion_food(food_name, calories_per_portion, self.now())

    def add_eaten_food(self, food: WeightedFood, weight_grams: Decimal) -> None:
        eaten_weighted_food = EatenWeightedFood(food, self.now(), weight_grams)
        Repository().add_eaten_weighted_food(eaten_weighted_food)

    def add_eaten_portion_food(self, portion_food: PortionFood) -> None:
        eaten_portion_food = EatenPortionFood(portion_food, self.now())
        Repository().add_eaten_portion_food(eaten_portion_food)

    def get_today_eaten_calories(self) -> Decimal:
        # Calculate eaten calories from 3 AM to 3 AM just in case of late dinner
        today = (self.now() - timedelta(hours=self.START_DATE_OFFSET_HOURS)).date()
        today_start_datetime = datetime(today.year, today.month, today.day, self.START_DATE_OFFSET_HOURS)
        eaten_foods = Repository().get_eaten_foods()
        today_eaten_calories = \
            [eaten_food.eaten_calories() for eaten_food in eaten_foods if eaten_food.added_on > today_start_datetime]
        today_eaten_calories_sum = sum(today_eaten_calories)
        return today_eaten_calories_sum

    @staticmethod
    def search_food(food_name) -> Optional[List[Food]]:
        foods = Repository().get_foods()
        candidates = [food for food in foods if food_name in food.name]
        return candidates
