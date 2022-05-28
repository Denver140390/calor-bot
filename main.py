from decimal import Decimal, InvalidOperation
from typing import Callable, List, Optional

from messageparser import MessageParser
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
ADD_NEW_FOOD = 'Add new food'
EDIT_FOOD = 'Edit food'
SHOW_EATEN_FOOD = 'Show eaten food'
ENTER_FOOD_NAME = 'Enter food name'
ENTER_FOOD_DATA = 'Enter food data'
CHOOSE_FROM_MULTIPLE_FOODS = 'Choose from multiple foods'
ENTER_FOOD_WEIGHT = 'Enter food weight'

FOOD_USER_DATA = 'food'
FOOD_NAME_USER_DATA = 'food_name'

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

service: Service = Service()


def try_parse_decimal(message: str) -> Optional[Decimal]:
    try:
        return Decimal(message)
    except InvalidOperation:
        return None


def start(update: Update, context: CallbackContext) -> str:
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    # Build InlineKeyboard where each button has a displayed text
    # and a string as callback_data
    # The keyboard is a list of button rows, where each row is in turn
    # a list (hence `[[...]]`).
    keyboard = init_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    update.message.reply_text(
        "Hello, my name is Calor and I wanna eat! Please feed me or at least tell me about food.",
        reply_markup=reply_markup)
    # Tell ConversationHandler that we're in state `FIRST` now
    return START_ROUTES


def start_over(update: Update, context: CallbackContext) -> str:
    # Build InlineKeyboard where each button has a displayed text
    # and a string as callback_data
    # The keyboard is a list of button rows, where each row is in turn
    # a list (hence `[[...]]`).
    keyboard = init_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    update.message.reply_text(
        "What is next?",
        reply_markup=reply_markup)
    # Tell ConversationHandler that we're in state `FIRST` now
    return START_ROUTES


def init_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(EAT, callback_data=str(EAT)),
            InlineKeyboardButton(ADD_NEW_FOOD, callback_data=str(ADD_NEW_FOOD)),
            InlineKeyboardButton(EDIT_FOOD, callback_data=str(EDIT_FOOD)),
            InlineKeyboardButton(SHOW_EATEN_FOOD, callback_data=str(SHOW_EATEN_FOOD))
        ]
    ]
    return keyboard


def eat(update: Update, context: CallbackContext) -> str:
    # text = context.args
    # command = MessageParser.parse(text)
    # service.add_total_calories_eaten_item(command)
    context.bot.send_message(chat_id=update.effective_chat.id, text="What am I going to eat?")
    return ENTER_FOOD_NAME


def enter_food_name(update: Update, context: CallbackContext) -> str:
    food_name = update.message.text.strip()
    context.user_data[FOOD_NAME_USER_DATA] = food_name
    candidates = service.search_food_item(food_name)
    if not candidates:
        update.message.reply_text("How many calories per 100 grams?")
        return ENTER_FOOD_DATA
    if len(candidates) > 1:
        update.message.reply_text(
            f"I know multiple of entries matching {food_name}. Can you please tell me a more specific name?")
        return ENTER_FOOD_DATA
        # TODO return CHOOSE_FROM_MULTIPLE_FOODS
    food = candidates[0]
    update.message.reply_text(f"I know already ate {food.name}, how many grams am I going to eat?")
    context.user_data[FOOD_USER_DATA] = food
    return ENTER_FOOD_WEIGHT


def enter_food_data(update: Update, context: CallbackContext) -> str:
    calories_per_100_grams_str = update.message.text.strip()
    calories_per_100_grams = try_parse_decimal(calories_per_100_grams_str)
    if not calories_per_100_grams:
        update.message.reply_text(
            "This does not seem as a number, can you please tell me a number of calories per 100 grams?")
        return ENTER_FOOD_DATA
    food_name = context.user_data[FOOD_NAME_USER_DATA]
    food = service.add_food_item(food_name, calories_per_100_grams)
    context.user_data[FOOD_USER_DATA] = food
    update.message.reply_text("How many grams will I eat?")
    return ENTER_FOOD_WEIGHT


def choose_from_multiple_foods(update: Update, context: CallbackContext) -> str:
    pass


def enter_food_weight(update: Update, context: CallbackContext) -> str:
    food_weight_str = update.message.text.strip()
    weight_grams = try_parse_decimal(food_weight_str)
    if not weight_grams:
        update.message.reply_text("This does not seem as a number, can you please tell me a number of grams?")
        return ENTER_FOOD_WEIGHT
    food = context.user_data[FOOD_USER_DATA]
    service.add_weighted_eaten_item(food, weight_grams)
    today_eaten_calories = service.get_today_eaten_calories()
    update.message.reply_text(f'Today I ate {today_eaten_calories} cal.')
    return start_over(update, context)


def new_food(update: Update, context: CallbackContext) -> str:
    pass


def edit_food(update: Update, context: CallbackContext) -> str:
    pass


def show_eaten_food(update: Update, context: CallbackContext) -> str:
    today_eaten_calories = service.get_today_eaten_calories()
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Today I ate {today_eaten_calories} cal.')
    return START_ROUTES


# def get_command_invoker(command: commands.Command) -> Optional[Callable[[commands.Command], List[str]]]:
#     if isinstance(command, commands.AddWeightCommand):
#         return lambda c: service.add_weight(c)
#     elif isinstance(command, commands.AddWeightedEatenItemCommand):
#         return lambda c: service.add_weighted_eaten_item(c)
#     elif isinstance(command, commands.AddTotalCaloriesEatenItemCommand):
#         return lambda c: service.add_total_calories_eaten_item(c)
#     return None


# def process_message(update: Update, context: CallbackContext):
#     text = update.message.text
#     command = MessageParser.parse(text)
#     if not command:
#         context.bot.send_message(chat_id=update.effective_chat.id, text='Unknown message pattern.')
#         return
#
#     command_invoker = get_command_invoker(command)
#     if not command_invoker:
#         context.bot.send_message(
#             chat_id=update.effective_chat.id,
#             text=f'Something went wrong, got no handler for {type(command)}.')
#         return
#     response_messages = command_invoker(command)
#     [context.bot.send_message(chat_id=update.effective_chat.id, text=response) for response in response_messages]


def process_message(update: Update, context: CallbackContext):
    text = update.message.text
    weight = try_parse_decimal(text)
    if not weight:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Unknown message pattern.')
        return
    response_messages = service.add_weight(weight)
    [context.bot.send_message(chat_id=update.effective_chat.id, text=response) for response in response_messages]


def echo(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


def unknown(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


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
            CallbackQueryHandler(new_food, pattern=f"^{ADD_NEW_FOOD}$"),
            CallbackQueryHandler(edit_food, pattern=f"^{EDIT_FOOD}$"),
            CallbackQueryHandler(show_eaten_food, pattern=f"^{SHOW_EATEN_FOOD}$"),
        ],
        ENTER_FOOD_NAME: [
            MessageHandler(Filters.text, enter_food_name)
        ],
        ENTER_FOOD_DATA: [
            MessageHandler(Filters.text, enter_food_data)
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
