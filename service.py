from collections import defaultdict
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
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

    @staticmethod
    def today_datetime() -> datetime:
        today = date.today()  # TODO client timezone
        return datetime.combine(today, datetime.min.time())

    def add_weight(self, weight_kilograms: Decimal, telegram_user_id: str) -> List[str]:
        weight = Weight(weight_kilograms, self.now())
        Repository().add_weight(weight, telegram_user_id)
        weights = Repository().get_weights_desc(telegram_user_id)
        response = f'Your current weight is {weight.weight_kilograms} kg. Got it!'
        if len(weights) == 1:
            return [response]
        else:
            # TODO can be multiple entries per day, gotta select first per yesterday
            return [f'{response} Previously it was {weights[1].weight_kilograms} kg.']

    def add_weighted_food(self, food_name: str, calories_per_100_grams: Decimal, telegram_user_id: str) -> WeightedFood:
        return Repository().add_weighted_food(food_name, calories_per_100_grams, self.now(), telegram_user_id)

    def add_portion_food(self, food_name: str, calories_per_portion: Decimal, telegram_user_id: str) -> PortionFood:
        return Repository().add_portion_food(food_name, calories_per_portion, self.now(), telegram_user_id)

    def add_eaten_food(self, food: WeightedFood, weight_grams: Decimal, telegram_user_id: str) -> None:
        eaten_weighted_food = EatenWeightedFood(food, self.now(), weight_grams)
        Repository().add_eaten_weighted_food(eaten_weighted_food, telegram_user_id)

    def add_eaten_portion_food(self, portion_food: PortionFood, telegram_user_id: str) -> None:
        eaten_portion_food = EatenPortionFood(portion_food, self.now())
        Repository().add_eaten_portion_food(eaten_portion_food, telegram_user_id)

    def get_eaten_calories_by_date(self, since_days_ago: int, telegram_user_id: str) -> dict[date, Decimal]:
        since = self.today_datetime() - timedelta(days=since_days_ago) + timedelta(hours=self.START_DATE_OFFSET_HOURS)
        eaten_foods = Repository().get_eaten_foods(since, telegram_user_id)
        eaten_food_by_date: defaultdict[date, Decimal] = defaultdict[date, Decimal](lambda: Decimal(0))
        for eaten_food in eaten_foods:
            # Calculate eaten calories from 3 AM to 3 AM just in case of late dinner
            eaten_food_date = (eaten_food.added_on - timedelta(hours=self.START_DATE_OFFSET_HOURS)).date()
            eaten_food_by_date[eaten_food_date] += eaten_food.eaten_calories()
        return eaten_food_by_date

    @staticmethod
    def get_food(food_id: int, telegram_user_id: str) -> Food:
        return Repository().get_food(food_id, telegram_user_id)

    @staticmethod
    def find_food(food_name: str, telegram_user_id: str) -> Food:
        return Repository().find_food(food_name, telegram_user_id)

    @staticmethod
    def search_food(food_name: str, telegram_user_id: str) -> Optional[Tuple[Food]]:
        foods = Repository().get_foods(telegram_user_id)
        candidates = []
        for food in foods:
            food_name_parts = food_name.split()  # TODO search in db
            is_all_food_name_parts_matched: bool = True
            for food_name_part in food_name_parts:
                if food_name_part not in food.name:
                    is_all_food_name_parts_matched = False
                    break
            if is_all_food_name_parts_matched:
                candidates.append(food)
        return tuple(candidates)
