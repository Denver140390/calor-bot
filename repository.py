from datetime import datetime
from decimal import Decimal
from typing import List
from models import Weight, Food, EatenFood
import os
import pyodbc


class Repository:

    def __init__(self):
        pass

    def add_weight(self, weight: Weight):
        sql = f"INSERT INTO dbo.Weight " \
              f"(UserId, WeightKilograms, AddedOn) VALUES " \
              f"(\'dm\', {weight.weight_kilograms}, \'{weight.added_on}\')"
        self.__connect().cursor().execute(sql).commit()

    def get_weights_desc(self) -> List[Weight]:
        sql = f"SELECT WeightKilograms, AddedOn FROM dbo.Weight ORDER BY AddedOn DESC"
        weight_rows = self.__connect().cursor().execute(sql).fetchall()
        weights = [Weight(row.WeightKilograms, row.AddedOn) for row in weight_rows]
        return weights

    def add_food(self, name: str, calories_per_100_grams: Decimal, added_on: datetime) -> Food:
        sql = ("INSERT INTO dbo.Food "
               "(UserId, Name, CaloriesPer100Grams, AddedOn)"
               "OUTPUT INSERTED.ID "
               "VALUES (?, ?, ?, ?)")
        cursor = self.__connect().cursor().execute(sql, 'dm', name, calories_per_100_grams, added_on)
        inserted_id = cursor.fetchval()
        cursor.commit()
        return Food(inserted_id, name, calories_per_100_grams, added_on)

    def get_foods(self) -> List[Food]:
        sql = f"SELECT Id, Name, CaloriesPer100Grams, AddedOn FROM dbo.Food ORDER BY AddedOn DESC"
        food_rows = self.__connect().cursor().execute(sql).fetchall()
        foods = [Food(row.Id, row.Name, row.CaloriesPer100Grams, row.AddedOn) for row in food_rows]
        return foods

    def add_eaten_food(self, eaten_food: EatenFood):
        sql = f'INSERT INTO dbo.EatenFood' \
              f'(UserId, FoodId, WeightGrams, AddedOn) VALUES' \
              f'(\'dm\', \'{eaten_food.food.id}\', {eaten_food.weight_grams}, \'{eaten_food.added_on}\')'
        self.__connect().cursor().execute(sql).commit()

    def get_eaten_foods(self) -> List[EatenFood]:
        sql = (f"SELECT Food.Id, Food.Name, Food.CaloriesPer100Grams, Food.AddedOn, "
               f"EatenFood.WeightGrams, EatenFood.AddedOn "
               f"FROM dbo.EatenFood "
               f"JOIN Food ON Food.Id = EatenFood.FoodId "
               f"ORDER BY EatenFood.AddedOn DESC")
        eaten_food_rows = self.__connect().cursor().execute(sql).fetchall()
        eaten_foods = [
            EatenFood(Food(row.Id, row.Name, row.CaloriesPer100Grams, row.AddedOn), row.WeightGrams, row.AddedOn)
            for row in eaten_food_rows]
        return eaten_foods

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
