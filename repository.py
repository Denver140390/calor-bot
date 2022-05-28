from datetime import datetime
from decimal import Decimal
from typing import List
from models import Weight, WeightedFood, EatenFood, EatenWeightedFood, Food, PortionFood, EatenPortionFood
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

    def add_weighted_food(self, food_name: str, calories_per_100_grams: Decimal, added_on: datetime) -> WeightedFood:
        sql = ("INSERT INTO dbo.Food "
               "(UserId, Name, CaloriesPer100Grams, AddedOn)"
               "OUTPUT INSERTED.ID "
               "VALUES (?, ?, ?, ?)")
        cursor = self.__connect().cursor().execute(sql, 'dm', food_name, calories_per_100_grams, added_on)
        inserted_id = cursor.fetchval()
        cursor.commit()
        return WeightedFood(inserted_id, food_name, added_on, calories_per_100_grams)

    def add_portion_food(self, food_name: str, calories_per_portion: Decimal, added_on: datetime) -> PortionFood:
        sql = ("INSERT INTO dbo.Food "
               "(UserId, Name, CaloriesPerPortion, AddedOn)"
               "OUTPUT INSERTED.ID "
               "VALUES (?, ?, ?, ?)")
        cursor = self.__connect().cursor().execute(sql, 'dm', food_name, calories_per_portion, added_on)
        inserted_id = cursor.fetchval()
        cursor.commit()
        return PortionFood(inserted_id, food_name, added_on, calories_per_portion)

    def get_foods(self) -> List[Food]:
        sql = f"SELECT Id, Name, CaloriesPer100Grams, CaloriesPerPortion, AddedOn FROM dbo.Food ORDER BY AddedOn DESC"
        food_rows = self.__connect().cursor().execute(sql).fetchall()
        weighted_foods: List[Food] = [
            WeightedFood(row.Id, row.Name, row.AddedOn, row.CaloriesPer100Grams)
            for row in food_rows if row.CaloriesPer100Grams]
        portion_foods: List[Food] = [
            PortionFood(row.Id, row.Name, row.AddedOn, row.CaloriesPerPortion)
            for row in food_rows if row.CaloriesPerPortion]
        return weighted_foods + portion_foods

    def add_eaten_weighted_food(self, eaten_weighted_food: EatenWeightedFood):
        sql = f'INSERT INTO dbo.EatenFood' \
              f'(UserId, FoodId, WeightGrams, AddedOn) VALUES' \
              f'(\'dm\', ' \
              f'\'{eaten_weighted_food.food.id}\', ' \
              f'{eaten_weighted_food.weight_grams}, ' \
              f'\'{eaten_weighted_food.added_on}\')'
        self.__connect().cursor().execute(sql).commit()

    def add_eaten_portion_food(self, eaten_portion_food: EatenPortionFood) -> None:
        sql = f'INSERT INTO dbo.EatenFood' \
              f'(UserId, FoodId, AddedOn) VALUES' \
              f'(\'dm\', ' \
              f'\'{eaten_portion_food.food.id}\', ' \
              f'\'{eaten_portion_food.added_on}\')'
        self.__connect().cursor().execute(sql).commit()

    def get_eaten_foods(self) -> List[EatenFood]:
        sql = (f"SELECT Food.Id, Food.Name, Food.CaloriesPer100Grams, Food.CaloriesPerPortion, Food.AddedOn, "
               f"EatenFood.WeightGrams, EatenFood.AddedOn "
               f"FROM dbo.EatenFood "
               f"JOIN Food ON Food.Id = EatenFood.FoodId "
               f"ORDER BY EatenFood.AddedOn DESC")
        eaten_food_rows = self.__connect().cursor().execute(sql).fetchall()
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
