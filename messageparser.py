from decimal import Decimal, InvalidOperation
from typing import Optional
import commands


class MessageParser:

    def __init__(self):
        pass

    @staticmethod
    def __try_parse_decimal(message: str) -> Optional[Decimal]:
        try:
            return Decimal(message)
        except InvalidOperation:
            return None

    @staticmethod
    def parse(message: str) -> Optional[commands.Command]:
        message = message.strip()

        weight = MessageParser.__try_parse_decimal(message)
        if weight:
            return commands.AddWeightCommand(weight)

        message_parts = message.split(' ')
        # TODO Кебаб 220 160 leads to second case, tho it has to be AddWeightedEatenItemCommand
        if len(message_parts) > 3:
            calories_per_100_grams = MessageParser.__try_parse_decimal(message_parts[-2])
            weight_grams = MessageParser.__try_parse_decimal(message_parts[-1])
            if calories_per_100_grams and weight_grams:
                dish_name = message.rstrip(message_parts[-1]).rstrip().rstrip(message_parts[-2]).rstrip()
                return commands.AddWeightedEatenItemCommand(dish_name, calories_per_100_grams, weight_grams)

        if len(message_parts) > 2:
            total_calories = MessageParser.__try_parse_decimal(message_parts[-1])
            if total_calories:
                dish_name = message.rstrip(message_parts[-1]).rstrip()
                return commands.AddTotalCaloriesEatenItemCommand(dish_name, total_calories)

        return None
