from datetime import datetime
from decimal import Decimal
from typing import List
from items import Weight, FoodItem, EatenItem
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

    def add_food_item(self, name: str, calories_per_100_grams: Decimal, added_on: datetime) -> FoodItem:
        sql = ("INSERT INTO dbo.FoodItem "
               "(UserId, Name, CaloriesPer100Grams, AddedOn)"
               "OUTPUT INSERTED.ID "
               "VALUES (?, ?, ?, ?)")
        cursor = self.__connect().cursor().execute(sql, 'dm', name, calories_per_100_grams, added_on)
        inserted_id = cursor.fetchval()
        cursor.commit()
        return FoodItem(inserted_id, name, calories_per_100_grams, added_on)

    def get_food_items(self) -> List[FoodItem]:
        sql = f"SELECT Id, Name, CaloriesPer100Grams, AddedOn FROM dbo.FoodItem ORDER BY AddedOn DESC"
        food_item_rows = self.__connect().cursor().execute(sql).fetchall()
        food_items = [FoodItem(row.Id, row.Name, row.CaloriesPer100Grams, row.AddedOn) for row in food_item_rows]
        return food_items

    def add_eaten_item(self, eaten_item: EatenItem):
        sql = f'INSERT INTO dbo.EatenFoodItem' \
              f'(UserId, FoodItemId, WeightGrams, AddedOn) VALUES' \
              f'(\'dm\', \'{eaten_item.item.id}\', {eaten_item.weight_grams}, \'{eaten_item.added_on}\')'
        self.__connect().cursor().execute(sql).commit()

    def get_eaten_items(self) -> List[EatenItem]:
        sql = (f"SELECT FoodItem.Id, FoodItem.Name, FoodItem.CaloriesPer100Grams, FoodItem.AddedOn, "
               f"EatenFoodItem.WeightGrams, EatenFoodItem.AddedOn "
               f"FROM dbo.EatenFoodItem "
               f"JOIN FoodItem ON FoodItem.Id = EatenFoodItem.FoodItemId "
               f"ORDER BY EatenFoodItem.AddedOn DESC")
        eaten_item_rows = self.__connect().cursor().execute(sql).fetchall()
        eaten_items = [
            EatenItem(FoodItem(row.Id, row.Name, row.CaloriesPer100Grams, row.AddedOn), row.WeightGrams, row.AddedOn)
            for row in eaten_item_rows]
        return eaten_items

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
