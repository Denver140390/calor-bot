from decimal import Decimal, InvalidOperation
from typing import Optional

from models import PortionFood, WeightedFood
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

# Stages
START_ROUTES, END_ROUTES = range(2)

EAT = 'Eat'
EAT_PORTION = 'Eat Portion'
ADD_NEW_FOOD = 'Add new food'
EDIT_FOOD = 'Edit food'
SHOW_EATEN_CALORIES = 'Show eaten calories'
ENTER_FOOD_NAME = 'Enter food name'
ENTER_PORTION_FOOD_NAME = 'Enter portion food name'
ENTER_FOOD_DATA = 'Enter food data'
ENTER_PORTION_FOOD_DATA = 'Enter portion food data'
CHOOSE_FROM_MULTIPLE_FOODS = 'Choose from multiple foods'
ENTER_FOOD_WEIGHT = 'Enter food weight'

FOOD_USER_DATA = 'food'
FOOD_NAME_USER_DATA = 'food_name'

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
    keyboard = init_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Hello, my name is Calor and I wanna eat! Please feed me or at least tell me about food.",
        reply_markup=reply_markup)
    return START_ROUTES


# noinspection PyUnusedLocal
def start_over(update: Update, context: CallbackContext) -> str:
    keyboard = init_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="What is next?",
        reply_markup=reply_markup)
    return START_ROUTES


def init_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(EAT, callback_data=str(EAT)),
            InlineKeyboardButton(EAT_PORTION, callback_data=str(EAT_PORTION))
        ],
        [
            InlineKeyboardButton(SHOW_EATEN_CALORIES, callback_data=str(SHOW_EATEN_CALORIES)),
            InlineKeyboardButton(ADD_NEW_FOOD, callback_data=str(ADD_NEW_FOOD)),
            InlineKeyboardButton(EDIT_FOOD, callback_data=str(EDIT_FOOD))
        ]
    ]
    return keyboard


def eat(update: Update, context: CallbackContext) -> str:
    context.bot.send_message(chat_id=update.effective_chat.id, text="What am I going to eat?")
    return ENTER_FOOD_NAME


def enter_food_name(update: Update, context: CallbackContext) -> str:
    food_name = update.message.text.strip()
    context.user_data[FOOD_NAME_USER_DATA] = food_name
    candidates = service.search_food(food_name, update.effective_user.id)
    if not candidates:
        update.message.reply_text("How many calories per 100 grams?")
        return ENTER_FOOD_DATA
    if len(candidates) > 1:
        update.message.reply_text(
            f"I know multiple of entries matching {food_name}. Can you please tell me a more specific name?")
        return ENTER_FOOD_NAME
    food = candidates[0]
    if not isinstance(food, WeightedFood):
        update.message.reply_text(
            f"This does not seem as a weighted food. Can you please tell me a more specific name?")
        return ENTER_FOOD_NAME
    weighted_food = food
    update.message.reply_text(f"I know already ate {weighted_food.name}, how many grams am I going to eat?")
    context.user_data[FOOD_USER_DATA] = weighted_food
    return ENTER_FOOD_WEIGHT


def enter_food_data(update: Update, context: CallbackContext) -> str:
    calories_per_100_grams_str = update.message.text.strip()
    calories_per_100_grams = try_parse_decimal(calories_per_100_grams_str)
    if not calories_per_100_grams:
        update.message.reply_text(
            "This does not seem as a number, can you please tell me a number of calories per 100 grams?")
        return ENTER_FOOD_DATA
    food_name = context.user_data[FOOD_NAME_USER_DATA]
    food = service.add_weighted_food(food_name, calories_per_100_grams, update.effective_user.id)
    context.user_data[FOOD_USER_DATA] = food
    update.message.reply_text("How many grams will I eat?")
    return ENTER_FOOD_WEIGHT


def eat_portion(update: Update, context: CallbackContext) -> str:
    context.bot.send_message(chat_id=update.effective_chat.id, text="What am I going to eat?")
    return ENTER_PORTION_FOOD_NAME


def enter_portion_food_name(update: Update, context: CallbackContext) -> str:
    food_name = update.message.text.strip()
    context.user_data[FOOD_NAME_USER_DATA] = food_name
    candidates = service.search_food(food_name, update.effective_user.id)
    if not candidates:
        update.message.reply_text("How many calories?")
        return ENTER_PORTION_FOOD_DATA
    if len(candidates) > 1:
        update.message.reply_text(
            f"I know multiple of entries matching {food_name}. Can you please tell me a more specific name?")
        return ENTER_PORTION_FOOD_NAME
    food = candidates[0]
    if not isinstance(food, PortionFood):
        update.message.reply_text(
            f"This does not seem as a portion food. Can you please tell me a more specific name?")
        return ENTER_PORTION_FOOD_NAME
    portion_food = food
    update.message.reply_text(f"I know {portion_food.name}, thanks.")
    service.add_eaten_portion_food(portion_food, update.effective_user.id)
    today_eaten_calories = service.get_today_eaten_calories(update.effective_user.id)
    update.message.reply_text(f'Today I ate {today_eaten_calories} cal.')
    return start_over(update, context)


def enter_portion_food_data(update: Update, context: CallbackContext) -> str:
    calories_per_portion_str = update.message.text.strip()
    calories_per_portion = try_parse_decimal(calories_per_portion_str)
    if not calories_per_portion:
        update.message.reply_text(
            "This does not seem as a number, can you please tell me a number of calories per portion?")
        return ENTER_PORTION_FOOD_DATA
    food_name = context.user_data[FOOD_NAME_USER_DATA]
    portion_food = service.add_portion_food(food_name, calories_per_portion, update.effective_user.id)
    service.add_eaten_portion_food(portion_food, update.effective_user.id)
    today_eaten_calories = service.get_today_eaten_calories(update.effective_user.id)
    update.message.reply_text(f'Today I ate {today_eaten_calories} cal.')
    return start_over(update, context)


# noinspection PyUnusedLocal
def choose_from_multiple_foods(update: Update, context: CallbackContext) -> str:
    pass


def enter_food_weight(update: Update, context: CallbackContext) -> str:
    food_weight_str = update.message.text.strip()
    weight_grams = try_parse_decimal(food_weight_str)
    if not weight_grams:
        update.message.reply_text("This does not seem as a number, can you please tell me a number of grams?")
        return ENTER_FOOD_WEIGHT
    food = context.user_data[FOOD_USER_DATA]
    service.add_eaten_food(food, weight_grams, update.effective_user.id)
    today_eaten_calories = service.get_today_eaten_calories(update.effective_user.id)
    update.message.reply_text(f'Today I ate {today_eaten_calories} cal.')
    return start_over(update, context)


# noinspection PyUnusedLocal
def new_food(update: Update, context: CallbackContext) -> str:
    pass


# noinspection PyUnusedLocal
def edit_food(update: Update, context: CallbackContext) -> str:
    pass


def show_eaten_calories(update: Update, context: CallbackContext) -> str:
    today_eaten_calories = service.get_today_eaten_calories(update.effective_user.id)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Today I ate {today_eaten_calories} cal.')
    return start_over(update, context)


def process_message(update: Update, context: CallbackContext):
    text = update.message.text
    weight = try_parse_decimal(text)
    if not weight:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Unknown message pattern.')
        return
    response_messages = service.add_weight(weight, update.effective_user.id)
    [context.bot.send_message(chat_id=update.effective_chat.id, text=response) for response in response_messages]


def echo(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


def unknown(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


# noinspection SpellCheckingInspection
updater = Updater(token=os.environ['TELEGRAMTOKEN'])
dispatcher = updater.dispatcher

# dispatcher.add_handler(CommandHandler('food', food))
# dispatcher.add_handler(CommandHandler('eat', eat))

# echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
# dispatcher.add_handler(echo_handler)

# dispatcher.add_handler(MessageHandler(~Filters.command, process_message))
# dispatcher.add_handler(MessageHandler(Filters.command, unknown))

dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        START_ROUTES: [
            CallbackQueryHandler(eat, pattern=f"^{EAT}$"),
            CallbackQueryHandler(eat_portion, pattern=f"^{EAT_PORTION}$"),
            CallbackQueryHandler(new_food, pattern=f"^{ADD_NEW_FOOD}$"),
            CallbackQueryHandler(edit_food, pattern=f"^{EDIT_FOOD}$"),
            CallbackQueryHandler(show_eaten_calories, pattern=f"^{SHOW_EATEN_CALORIES}$"),
        ],
        ENTER_FOOD_NAME: [
            MessageHandler(Filters.text, enter_food_name)
        ],
        ENTER_PORTION_FOOD_NAME: [
            MessageHandler(Filters.text, enter_portion_food_name)
        ],
        ENTER_FOOD_DATA: [
            MessageHandler(Filters.text, enter_food_data)
        ],
        ENTER_PORTION_FOOD_DATA: [
            MessageHandler(Filters.text, enter_portion_food_data)
        ],
        CHOOSE_FROM_MULTIPLE_FOODS: [
            MessageHandler(Filters.text, choose_from_multiple_foods)
        ],
        ENTER_FOOD_WEIGHT: [
            MessageHandler(Filters.text, enter_food_weight)
        ]
    },
    fallbacks=[CommandHandler("start", start)],
))

updater.start_polling()

# updater.stop()
