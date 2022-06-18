from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple, List
from collections import defaultdict
from models import PortionFood, WeightedFood, Food
from service import Service
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
)
import logging
import os

SHOW_EATEN_CALORIES_SINCE_DAYS_AGO = 6

# Stages
START_ROUTES, END_ROUTES = range(2)
CHOOSE_FOOD_TYPE = 'Choose food type'
NEW_WEIGHTED_FOOD = 'Weighted'
NEW_PORTION_FOOD = 'Portion'
NEW_QUANTITY_FOOD = 'Quantity'
NEW_COMPOSITION_FOOD = 'Composition'

EAT_ADDED_FOOD = 'Eat added food'
EAT_FOUND_FOOD = 'Eat found food'
ADD_WITH_SAME_NAME = 'Add with same name'
START_OVER = 'Start over'
START_OVER_OR_EAT_ADDED_FOOD = 'START_OVER_OR_EAT_ADDED_FOOD'
ADD_SAME_OR_EAT_OR_START_OVER = 'ADD_SAME_OR_EAT_OR_START_OVER'

EAT = 'Eat'
ADD_NEW_FOOD = 'Add new food'
EDIT_FOOD = 'Edit food'
SHOW_EATEN_CALORIES = 'Show eaten calories'
ENTER_FOOD_NAME_TO_EAT = 'Enter food name'
ENTER_NEW_FOOD_NAME = 'Enter new food name'
ENTER_NEW_WEIGHTED_FOOD_DATA = 'Enter new weighted food data'
ENTER_NEW_PORTION_FOOD_DATA = 'Enter new portion food data'
CHOOSE_FROM_MULTIPLE_FOODS = 'Choose from multiple foods'
ENTER_FOOD_WEIGHT = 'Enter food weight'
ADD_WEIGHT = 'Add weight'
ENTER_WEIGHT = 'Enter weight'

EAT_FOOD_AFTER_ADDING_USER_DATA = 'EAT_FOOD_AFTER_ADDING_USER_DATA'
FOOD_USER_DATA = 'FOOD_USER_DATA'
FOOD_NAME_USER_DATA = 'FOOD_NAME_USER_DATA'
IS_NEW_FOOD_WITH_SAME_NAME_ALLOWED_USER_DATA = 'ALLOWED_NEW_FOOD_WITH_SAME_NAME_USER_DATA'

# TODO query.answer() to stop loaded? https://core.telegram.org/bots/api#callbackquery

# noinspection SpellCheckingInspection
# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

service: Service = Service()


def try_parse_decimal(message: str) -> Optional[Decimal]:
    try:
        return Decimal(message)
    except InvalidOperation:
        return None


# noinspection PyUnusedLocal
def start(update: Update, context: CallbackContext) -> str:
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    keyboard = get_start_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Hello, my name is Calor and I wanna eat! Please feed me or at least tell me about food.",
        reply_markup=reply_markup)
    return START_ROUTES


# noinspection PyUnusedLocal
def start_over(update: Update, context: CallbackContext) -> str:
    keyboard = get_start_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="What is next?",
        reply_markup=reply_markup)
    return START_ROUTES


def get_start_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(EAT, callback_data=EAT)
        ],
        [
            InlineKeyboardButton(SHOW_EATEN_CALORIES, callback_data=SHOW_EATEN_CALORIES),
            InlineKeyboardButton(ADD_NEW_FOOD, callback_data=ADD_NEW_FOOD),
            InlineKeyboardButton(EDIT_FOOD, callback_data=EDIT_FOOD)
        ],
        [
            InlineKeyboardButton(ADD_WEIGHT, callback_data=ADD_WEIGHT)
        ]
    ]
    return keyboard


def get_food_type_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(NEW_WEIGHTED_FOOD, callback_data=NEW_WEIGHTED_FOOD),
            InlineKeyboardButton(NEW_PORTION_FOOD, callback_data=NEW_PORTION_FOOD)
        ],
        [
            InlineKeyboardButton(NEW_QUANTITY_FOOD, callback_data=NEW_QUANTITY_FOOD),
            InlineKeyboardButton(NEW_COMPOSITION_FOOD, callback_data=NEW_COMPOSITION_FOOD),
        ],
        [
            InlineKeyboardButton(START_OVER, callback_data=START_OVER)
        ]
    ]
    return keyboard


def get_add_same_or_eat_or_start_over_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(ADD_WITH_SAME_NAME, callback_data=ADD_WITH_SAME_NAME),
            InlineKeyboardButton(EAT_FOUND_FOOD, callback_data=EAT_FOUND_FOOD)
        ],
        [
            InlineKeyboardButton(START_OVER, callback_data=START_OVER)
        ]
    ]
    return keyboard


def get_eat_or_start_over_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(EAT_ADDED_FOOD, callback_data=EAT_ADDED_FOOD),
            InlineKeyboardButton(START_OVER, callback_data=START_OVER)
        ]
    ]
    return keyboard


def get_food_names_keyboard(foods: Tuple[Food]):
    foods_sorted = sorted(foods, key=lambda food: food.name + str(food.added_on))
    food_name_by_count: defaultdict[str, int] = defaultdict[str, int](lambda: 0)
    for f in foods:
        food_name_by_count[f.name] += 1
    keyboard: List[List[InlineKeyboardButton]] = []
    for f in foods_sorted:
        food_name = f.name if food_name_by_count[f.name] == 1 else f"{f.name} {f.added_on.date()}"
        keyboard.append([InlineKeyboardButton(food_name, callback_data=f.id)])
    keyboard.append([InlineKeyboardButton(START_OVER, callback_data=START_OVER)])
    return keyboard


def get_eaten_calories_text(eaten_calories: dict[date, Decimal]) -> str:
    eaten_calories_strings: List[str] = []
    for calories_date, calories in eaten_calories.items():
        eaten_calories_strings.append(f"{calories_date}: {calories} cal")
    return "\n".join(eaten_calories_strings)


def eat(update: Update, context: CallbackContext) -> str:
    context.bot.send_message(chat_id=update.effective_chat.id, text="Food name?")
    return ENTER_FOOD_NAME_TO_EAT


def enter_food_name_to_eat(update: Update, context: CallbackContext) -> str:
    food_name = update.message.text.strip()
    context.user_data[FOOD_NAME_USER_DATA] = food_name
    candidates = service.search_food(food_name, update.effective_user.id)
    if not candidates:
        context.user_data[EAT_FOOD_AFTER_ADDING_USER_DATA] = None  # the value does not matter, just adding a key
        update.message.reply_text("Food type?", reply_markup=InlineKeyboardMarkup(get_food_type_keyboard()))
        return CHOOSE_FOOD_TYPE
    if len(candidates) > 1:
        update.message.reply_text(
            text="Which one?",
            reply_markup=InlineKeyboardMarkup(get_food_names_keyboard(candidates)))
        return CHOOSE_FROM_MULTIPLE_FOODS
    food = candidates[0]
    return eat_food(food, update, context)


def eat_food(food: Food, update: Update, context: CallbackContext) -> str:
    if isinstance(food, WeightedFood):
        return eat_weighted_food(food, update, context)
    if isinstance(food, PortionFood):
        return eat_portion_food(food, update, context)
    raise NotImplementedError("Unknown food type.")


def eat_food_from_context(update: Update, context: CallbackContext) -> str:
    food = context.user_data[FOOD_USER_DATA]
    if isinstance(food, WeightedFood):
        return eat_weighted_food(food, update, context)
    if isinstance(food, PortionFood):
        return eat_portion_food(food, update, context)
    raise NotImplementedError("Unknown food type.")


def eat_weighted_food(food: WeightedFood, update: Update, context: CallbackContext) -> str:
    context.user_data[FOOD_USER_DATA] = food
    context.bot.send_message(chat_id=update.effective_chat.id, text="How many grams?")
    return ENTER_FOOD_WEIGHT


def eat_portion_food(food: PortionFood, update: Update, context: CallbackContext) -> str:
    service.add_eaten_portion_food(food, update.effective_user.id)
    eaten_calories = service.get_eaten_calories_by_date(
        since_days_ago=SHOW_EATEN_CALORIES_SINCE_DAYS_AGO,
        telegram_user_id=update.effective_user.id)
    context.bot.send_message(chat_id=update.effective_chat.id, text=get_eaten_calories_text(eaten_calories))
    return start_over(update, context)


def choose_from_multiple_foods(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    food_id = int(query.data)
    food = service.get_food(food_id, update.effective_user.id)
    return eat_food(food, update, context)


def enter_food_weight(update: Update, context: CallbackContext) -> str:
    food_weight_str = update.message.text.strip()
    weight_grams = try_parse_decimal(food_weight_str)
    if not weight_grams:
        update.message.reply_text("This does not seem as a number, can you please tell me a number of grams?")
        return ENTER_FOOD_WEIGHT
    food = context.user_data[FOOD_USER_DATA]
    service.add_eaten_food(food, weight_grams, update.effective_user.id)
    eaten_calories = service.get_eaten_calories_by_date(
        since_days_ago=SHOW_EATEN_CALORIES_SINCE_DAYS_AGO,
        telegram_user_id=update.effective_user.id)
    update.message.reply_text(get_eaten_calories_text(eaten_calories))
    return start_over(update, context)


def new_food(update: Update, context: CallbackContext) -> str:
    context.bot.send_message(chat_id=update.effective_chat.id, text="Food name?")
    return ENTER_NEW_FOOD_NAME


def add_food_same_name(update: Update, context: CallbackContext) -> str:
    context.user_data[IS_NEW_FOOD_WITH_SAME_NAME_ALLOWED_USER_DATA] = None  # only key is used
    food_name = context.user_data[FOOD_NAME_USER_DATA]
    return enter_food_name(food_name, update, context)


def enter_new_food_name(update: Update, context: CallbackContext) -> str:
    food_name = update.message.text.strip()
    context.user_data[FOOD_NAME_USER_DATA] = food_name
    return enter_food_name(food_name, update, context)


def enter_food_name(food_name: str, update: Update, context: CallbackContext) -> str:
    food = service.find_food(food_name, update.effective_user.id)
    if food and IS_NEW_FOOD_WITH_SAME_NAME_ALLOWED_USER_DATA not in context.user_data:
        update.message.reply_text(
            f"I already know {food.name}.",
            reply_markup=InlineKeyboardMarkup(get_add_same_or_eat_or_start_over_keyboard()))
        context.user_data[FOOD_USER_DATA] = food
        del context.user_data[IS_NEW_FOOD_WITH_SAME_NAME_ALLOWED_USER_DATA]
        return ADD_SAME_OR_EAT_OR_START_OVER
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Food type?",
        reply_markup=InlineKeyboardMarkup(get_food_type_keyboard()))
    return CHOOSE_FOOD_TYPE


def new_weighted_food(update: Update, context: CallbackContext) -> str:
    context.bot.send_message(chat_id=update.effective_chat.id, text="How many calories per 100 grams?")
    return ENTER_NEW_WEIGHTED_FOOD_DATA


def enter_new_weighted_food_data(update: Update, context: CallbackContext) -> str:
    calories_per_100_grams_str = update.message.text.strip()
    calories_per_100_grams = try_parse_decimal(calories_per_100_grams_str)
    if not calories_per_100_grams:
        update.message.reply_text(
            "This does not seem as a number, can you please tell me a number of calories per 100 grams?")
        return ENTER_NEW_WEIGHTED_FOOD_DATA
    food_name = context.user_data[FOOD_NAME_USER_DATA]
    food = service.add_weighted_food(food_name, calories_per_100_grams, update.effective_user.id)
    return finish_adding_new_food(food, update, context)


def new_portion_food(update: Update, context: CallbackContext) -> str:
    context.bot.send_message(chat_id=update.effective_chat.id, text="How many calories in a portion?")
    return ENTER_NEW_PORTION_FOOD_DATA


def enter_new_portion_food_data(update: Update, context: CallbackContext) -> str:
    calories_per_portion_str = update.message.text.strip()
    calories_per_portion = try_parse_decimal(calories_per_portion_str)
    if not calories_per_portion:
        update.message.reply_text(
            "This does not seem as a number, can you please tell me a number of calories in a portion?")
        return ENTER_NEW_PORTION_FOOD_DATA
    food_name = context.user_data[FOOD_NAME_USER_DATA]
    food = service.add_portion_food(food_name, calories_per_portion, update.effective_user.id)
    return finish_adding_new_food(food, update, context)


def finish_adding_new_food(food: Food, update: Update, context: CallbackContext) -> str:
    if EAT_FOOD_AFTER_ADDING_USER_DATA in context.user_data:
        del context.user_data[EAT_FOOD_AFTER_ADDING_USER_DATA]
        return eat_food(food, update, context)
    update.message.reply_text(
        text="Eat added food or start over?",
        reply_markup=InlineKeyboardMarkup(get_eat_or_start_over_keyboard()))
    context.user_data[FOOD_USER_DATA] = food
    return START_OVER_OR_EAT_ADDED_FOOD


# noinspection PyUnusedLocal
def new_quantity_food(update: Update, context: CallbackContext) -> str:
    pass


# noinspection PyUnusedLocal
def new_composition_food(update: Update, context: CallbackContext) -> str:
    pass


# noinspection PyUnusedLocal
def edit_food(update: Update, context: CallbackContext) -> str:
    pass


def show_eaten_calories(update: Update, context: CallbackContext) -> str:
    eaten_calories = service.get_eaten_calories_by_date(
        since_days_ago=SHOW_EATEN_CALORIES_SINCE_DAYS_AGO,
        telegram_user_id=update.effective_user.id)
    context.bot.send_message(chat_id=update.effective_chat.id, text=get_eaten_calories_text(eaten_calories))
    return start_over(update, context)


def add_weight(update: Update, context: CallbackContext) -> str:
    context.bot.send_message(chat_id=update.effective_chat.id, text="Enter weight in kg")
    return ENTER_WEIGHT


def enter_weight(update: Update, context: CallbackContext) -> str:
    weight = try_parse_decimal(update.message.text)
    response_messages = service.add_weight(weight, update.effective_user.id)
    [context.bot.send_message(chat_id=update.effective_chat.id, text=response) for response in response_messages]
    return start_over(update, context)


# noinspection SpellCheckingInspection
updater = Updater(token=os.environ['TELEGRAMTOKEN'])
dispatcher = updater.dispatcher

dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        START_ROUTES: [
            CallbackQueryHandler(eat, pattern=f"^{EAT}$"),
            CallbackQueryHandler(new_food, pattern=f"^{ADD_NEW_FOOD}$"),
            CallbackQueryHandler(edit_food, pattern=f"^{EDIT_FOOD}$"),
            CallbackQueryHandler(show_eaten_calories, pattern=f"^{SHOW_EATEN_CALORIES}$"),
            CallbackQueryHandler(add_weight, pattern=f"^{ADD_WEIGHT}$"),
        ],
        CHOOSE_FOOD_TYPE: [
            CallbackQueryHandler(new_weighted_food, pattern=f"^{NEW_WEIGHTED_FOOD}$"),
            CallbackQueryHandler(new_portion_food, pattern=f"^{NEW_PORTION_FOOD}$"),
            CallbackQueryHandler(new_quantity_food, pattern=f"^{NEW_QUANTITY_FOOD}$"),
            CallbackQueryHandler(new_composition_food, pattern=f"^{NEW_COMPOSITION_FOOD}$"),
            CallbackQueryHandler(start_over, pattern=f"^{START_OVER}$")
        ],
        ENTER_FOOD_NAME_TO_EAT: [
            MessageHandler(Filters.text, enter_food_name_to_eat)
        ],
        ENTER_NEW_FOOD_NAME: [
            MessageHandler(Filters.text, enter_new_food_name)
        ],
        ENTER_NEW_WEIGHTED_FOOD_DATA: [
            MessageHandler(Filters.text, enter_new_weighted_food_data)
        ],
        ENTER_NEW_PORTION_FOOD_DATA: [
            MessageHandler(Filters.text, enter_new_portion_food_data)
        ],
        CHOOSE_FROM_MULTIPLE_FOODS: [
            CallbackQueryHandler(start_over, pattern=f"^{START_OVER}$"),
            CallbackQueryHandler(choose_from_multiple_foods)
        ],
        ENTER_FOOD_WEIGHT: [
            MessageHandler(Filters.text, enter_food_weight)
        ],
        ENTER_WEIGHT: [
            MessageHandler(Filters.text, enter_weight)
        ],
        START_OVER_OR_EAT_ADDED_FOOD: [
            CallbackQueryHandler(start_over, pattern=f"^{START_OVER}$"),
            CallbackQueryHandler(eat_food_from_context, pattern=f"^{EAT_ADDED_FOOD}$")
        ],
        ADD_SAME_OR_EAT_OR_START_OVER: [
            CallbackQueryHandler(start_over, pattern=f"^{START_OVER}$"),
            CallbackQueryHandler(eat_food_from_context, pattern=f"^{EAT_FOUND_FOOD}$"),
            CallbackQueryHandler(add_food_same_name, pattern=f"^{ADD_WITH_SAME_NAME}$")

        ]
    },
    fallbacks=[CommandHandler("start", start)],
))

updater.start_polling()

# updater.stop()
