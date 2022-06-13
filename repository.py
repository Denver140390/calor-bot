from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from models import Weight, WeightedFood, EatenFood, EatenWeightedFood, Food, PortionFood, EatenPortionFood
import os
import pyodbc


class Repository:

    def __init__(self):
        pass

    def add_weight(self, weight: Weight, telegram_user_id: str):
        sql = f"INSERT INTO dbo.Weight " \
              f"(TelegramUserId, WeightKilograms, AddedOn) VALUES " \
              f"(\'{telegram_user_id}\', {weight.weight_kilograms}, \'{weight.added_on}\')"
        self.__connect().cursor().execute(sql).commit()

    def get_weights_desc(self, telegram_user_id: str) -> List[Weight]:
        sql = f"SELECT WeightKilograms, AddedOn FROM dbo.Weight WHERE TelegramUserId = ? ORDER BY AddedOn DESC"
        weight_rows = self.__connect().cursor().execute(sql, telegram_user_id).fetchall()
        weights = [Weight(row.WeightKilograms, row.AddedOn) for row in weight_rows]
        return weights

    def add_weighted_food(
            self,
            food_name: str,
            calories_per_100_grams: Decimal,
            added_on: datetime,
            telegram_user_id: str) -> WeightedFood:
        sql = ("INSERT INTO dbo.Food "
               "(TelegramUserId, Name, CaloriesPer100Grams, AddedOn) "
               "OUTPUT INSERTED.ID "
               "VALUES (?, ?, ?, ?)")
        cursor = self.__connect().cursor().execute(sql, telegram_user_id, food_name, calories_per_100_grams, added_on)
        inserted_id = cursor.fetchval()
        cursor.commit()
        return WeightedFood(inserted_id, food_name, added_on, calories_per_100_grams)

    def add_portion_food(
            self, food_name: str,
            calories_per_portion: Decimal,
            added_on: datetime,
            telegram_user_id: str) -> PortionFood:
        sql = ("INSERT INTO dbo.Food "
               "(TelegramUserId, Name, CaloriesPerPortion, AddedOn) "
               "OUTPUT INSERTED.ID "
               "VALUES (?, ?, ?, ?)")
        cursor = self.__connect().cursor().execute(sql, telegram_user_id, food_name, calories_per_portion, added_on)
        inserted_id = cursor.fetchval()
        cursor.commit()
        return PortionFood(inserted_id, food_name, added_on, calories_per_portion)

    def get_food(self, food_id: int, telegram_user_id: str) -> Food:
        sql = (f"SELECT Id, Name, CaloriesPer100Grams, CaloriesPerPortion, AddedOn "
               f"FROM dbo.Food "
               f"WHERE Id = ? AND TelegramUserId = ? ")
        row = self.__connect().cursor().execute(sql, food_id, telegram_user_id).fetchone()
        if not row:
            raise RuntimeError(f"Unexpected error - could not find food by id {food_id}")

        if row.CaloriesPer100Grams:
            return WeightedFood(row.Id, row.Name, row.AddedOn, row.CaloriesPer100Grams)
        if row.CaloriesPerPortion:
            return PortionFood(row.Id, row.Name, row.AddedOn, row.CaloriesPerPortion)

        raise RuntimeError(f"Unexpected error - unknown food type by {id}")

    def find_food(self, food_name: str, telegram_user_id: str) -> Optional[Food]:
        sql = (f"SELECT Id, Name, CaloriesPer100Grams, CaloriesPerPortion, AddedOn "
               f"FROM dbo.Food "
               f"WHERE Name = ? AND TelegramUserId = ? ")
        row = self.__connect().cursor().execute(sql, food_name, telegram_user_id).fetchone()
        if not row:
            return None

        if row.CaloriesPer100Grams:
            return WeightedFood(row.Id, row.Name, row.AddedOn, row.CaloriesPer100Grams)
        if row.CaloriesPerPortion:
            return PortionFood(row.Id, row.Name, row.AddedOn, row.CaloriesPerPortion)

        raise RuntimeError(f"Unexpected error - unknown food type by {id}")

    def get_foods(self, telegram_user_id: str) -> List[Food]:
        sql = (f"SELECT Id, Name, CaloriesPer100Grams, CaloriesPerPortion, AddedOn "
               f"FROM dbo.Food "
               f"WHERE TelegramUserId = ? "
               f"ORDER BY AddedOn DESC")
        food_rows = self.__connect().cursor().execute(sql, telegram_user_id).fetchall()
        weighted_foods: List[Food] = [
            WeightedFood(row.Id, row.Name, row.AddedOn, row.CaloriesPer100Grams)
            for row in food_rows if row.CaloriesPer100Grams]
        portion_foods: List[Food] = [
            PortionFood(row.Id, row.Name, row.AddedOn, row.CaloriesPerPortion)
            for row in food_rows if row.CaloriesPerPortion]  # TODO exclude weighted_foods
        return weighted_foods + portion_foods

    def add_eaten_weighted_food(self, eaten_weighted_food: EatenWeightedFood, telegram_user_id: str):
        sql = f'INSERT INTO dbo.EatenFood' \
              f'(TelegramUserId, FoodId, WeightGrams, AddedOn) VALUES' \
              f'(\'{telegram_user_id}\', ' \
              f'\'{eaten_weighted_food.food.id}\', ' \
              f'{eaten_weighted_food.weight_grams}, ' \
              f'\'{eaten_weighted_food.added_on}\')'
        self.__connect().cursor().execute(sql).commit()

    def add_eaten_portion_food(self, eaten_portion_food: EatenPortionFood, telegram_user_id: str) -> None:
        sql = f'INSERT INTO dbo.EatenFood' \
              f'(TelegramUserId, FoodId, AddedOn) VALUES' \
              f'(\'{telegram_user_id}\', ' \
              f'\'{eaten_portion_food.food.id}\', ' \
              f'\'{eaten_portion_food.added_on}\')'
        self.__connect().cursor().execute(sql).commit()

    def get_eaten_foods(self, since: datetime, telegram_user_id: str) -> List[EatenFood]:
        sql = (f"SELECT Food.Id, Food.Name, Food.CaloriesPer100Grams, Food.CaloriesPerPortion, Food.AddedOn, "
               f"EatenFood.WeightGrams, EatenFood.AddedOn "
               f"FROM dbo.EatenFood "
               f"JOIN Food ON Food.Id = EatenFood.FoodId "
               f"WHERE EatenFood.AddedOn > ? AND EatenFood.TelegramUserId = ? "
               f"ORDER BY EatenFood.AddedOn DESC")
        eaten_food_rows = self.__connect().cursor().execute(sql, since, telegram_user_id).fetchall()
        eaten_weighted_foods: List[EatenFood] = [
            EatenWeightedFood(
                WeightedFood(row.Id, row.Name, row.AddedOn, row.CaloriesPer100Grams),
                row.AddedOn,
                row.WeightGrams)
            for row in eaten_food_rows if row.CaloriesPer100Grams]
        eaten_portion_foods: List[EatenFood] = [
            EatenPortionFood(
                PortionFood(row.Id, row.Name, row.AddedOn, row.CaloriesPerPortion),
                row.AddedOn)
            for row in eaten_food_rows if row.CaloriesPerPortion]
        return eaten_weighted_foods + eaten_portion_foods

    # noinspection SpellCheckingInspection
    @staticmethod
    def __connect() -> pyodbc.Connection:
        server = 'localhost'
        database = 'calor-bot-db'
        username = os.environ['DBUSERNAME']
        password = os.environ['DBPASSWORD']
        connection = pyodbc.connect(
            'DRIVER={ODBC Driver 18 for SQL Server}'
            ';SERVER=' + server +
            ';DATABASE=' + database +
            ';UID=' + username +
            ';PWD=' + password +
            ';TrustServerCertificate=YES')
        return connection
