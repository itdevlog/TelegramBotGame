from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import random
import datetime  # Для работы с временем

# Словарь для хранения загаданных чисел для каждого пользователя (для кубика)
user_numbers = {}

# Словарь для хранения статистики побед и поражений для игры "Кубик"
dice_stats = {}

# Словарь для хранения статистики побед и поражений для игры "Орёл или решка"
coin_stats = {}

# Словарь для хранения состояния игры "Крестики-нолики"
tic_tac_toe_games = {}
tic_tac_toe_stats = {}  # Статистика для "Крестики-нолики"

# Словарь для хранения состояния игры "Таблица умножения"
multiplication_games = {}
multiplication_stats = {}  # Статистика для "Таблица умножения"

# Функция для записи логов в файл
def log_to_file(username, action):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Текущее время
    with open("bot_logs.txt", "a", encoding="utf-8") as file:  # Открываем файл для дозаписи
        file.write(f"[{timestamp}] Пользователь {username}: {action}\n")

# Создаем клавиатуру с кнопками для выбора чисел от 1 до 6 (для кубика)
def dice_keyboard():
    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"guess_{i}") for i in range(1, 4)],
        [InlineKeyboardButton(str(i), callback_data=f"guess_{i}") for i in range(4, 7)],
        [InlineKeyboardButton("Назад", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Создаем клавиатуру для игры "Орёл или решка"
def coin_keyboard():
    keyboard = [
        [InlineKeyboardButton("Орёл", callback_data="coin_eagle"), InlineKeyboardButton("Решка", callback_data="coin_tails")],
        [InlineKeyboardButton("Назад", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Создаем главное меню
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Бросить кубик", callback_data="roll_dice")],
        [InlineKeyboardButton("Орёл или решка", callback_data="flip_coin")],
        [InlineKeyboardButton("Крестики-нолики", callback_data="tic_tac_toe")],
        [InlineKeyboardButton("Таблица умножения", callback_data="multiplication_table")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Создаем меню для игры "Кубик"
def dice_menu_keyboard(user_id):
    stats = dice_stats.get(user_id, {"wins": 0, "losses": 0})
    wins = stats["wins"]
    losses = stats["losses"]
    keyboard = [
        [InlineKeyboardButton(f"Статистика (Кубик): Побед - {wins}, Поражений - {losses}", callback_data="dice_stats")],
        [InlineKeyboardButton("Бросить кубик", callback_data="roll_dice")],
        [InlineKeyboardButton("Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Создаем меню для игры "Орёл или решка"
def coin_menu_keyboard(user_id):
    stats = coin_stats.get(user_id, {"wins": 0, "losses": 0})
    wins = stats["wins"]
    losses = stats["losses"]
    keyboard = [
        [InlineKeyboardButton(f"Статистика (Орёл/Решка): Побед - {wins}, Поражений - {losses}", callback_data="coin_stats")],
        [InlineKeyboardButton("Подбросить монетку", callback_data="flip_coin")],
        [InlineKeyboardButton("Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Создаем игровое поле для "Крестики-нолики"
def create_tic_tac_toe_keyboard(game_state):
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            cell = game_state[i * 3 + j]
            if cell == "":
                row.append(InlineKeyboardButton(f"{i * 3 + j + 1}", callback_data=f"ttt_move_{i * 3 + j}"))
            else:
                row.append(InlineKeyboardButton(cell, callback_data="none"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

# Проверка победителя в "Крестики-нолики"
def check_winner(game_state):
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # строки
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # столбцы
        [0, 4, 8], [2, 4, 6]              # диагонали
    ]
    for combo in winning_combinations:
        a, b, c = combo
        if game_state[a] == game_state[b] == game_state[c] and game_state[a] != "":
            return game_state[a]  # Возвращаем символ победителя ('X' или 'O')
    if "" not in game_state:
        return "draw"  # Ничья
    return None  # Игра продолжается

# Ход бота в "Крестики-нолики"
def bot_move(game_state):
    empty_cells = [i for i, cell in enumerate(game_state) if cell == ""]
    return random.choice(empty_cells)

# Создаем клавиатуру с вариантами ответов для "Таблицы умножения"
def create_multiplication_keyboard(multiplication_game):
    correct_answer = multiplication_game["num1"] * multiplication_game["num2"]
    options = [correct_answer]

    # Генерируем три неправильных варианта
    while len(options) < 4:
        wrong_answer = random.randint(1, 100)
        if wrong_answer not in options:
            options.append(wrong_answer)

    # Перемешиваем варианты
    random.shuffle(options)

    # Создаем клавиатуру
    keyboard = []
    for option in options:
        keyboard.append([InlineKeyboardButton(str(option), callback_data=f"mult_answer_{option}")])
    keyboard.append([InlineKeyboardButton("Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

# Меню для "Крестики-нолики"
def tic_tac_toe_menu_keyboard(user_id):
    stats = tic_tac_toe_stats.get(user_id, {"wins": 0, "losses": 0, "draws": 0})
    wins = stats["wins"]
    losses = stats["losses"]
    draws = stats["draws"]
    keyboard = [
        [InlineKeyboardButton(f"Статистика (Крестики-нолики): Побед - {wins}, Поражений - {losses}, Ничьих - {draws}", callback_data="tic_tac_toe_stats")],
        [InlineKeyboardButton("Начать игру", callback_data="tic_tac_toe")],
        [InlineKeyboardButton("Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню для "Таблица умножения"
def multiplication_menu_keyboard(user_id):
    stats = multiplication_stats.get(user_id, {"wins": 0, "losses": 0})
    wins = stats["wins"]
    losses = stats["losses"]
    keyboard = [
        [InlineKeyboardButton(f"Статистика (Таблица умножения): Побед - {wins}, Поражений - {losses}", callback_data="multiplication_stats")],
        [InlineKeyboardButton("Начать игру", callback_data="multiplication_table")],
        [InlineKeyboardButton("Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_game(update: Update, context) -> None:
    """Начинаем новую игру"""
    user = update.effective_user
    username = user.username if user.username else user.first_name  # Получаем имя пользователя
    log_to_file(username, "запустил бота")  # Записываем лог в файл

    reply_markup = main_menu_keyboard()
    await update.message.reply_text("Добро пожаловать в игру! Выбери действие:", reply_markup=reply_markup)

async def button_handler(update: Update, context) -> None:
    """Обработчик нажатия на кнопки"""
    query = update.callback_query
    await query.answer()  # Подтверждаем получение запроса

    user = query.from_user
    username = user.username if user.username else user.first_name  # Получаем имя пользователя

    user_id = query.from_user.id

    if query.data == "roll_dice":
        # Если пользователь выбрал "Бросить кубик", начинаем игру
        number_to_guess = random.randint(1, 6)  # Диапазон теперь от 1 до 6
        user_numbers[user_id] = number_to_guess  # Сохраняем число для пользователя
        stats = dice_stats.get(user_id, {"wins": 0, "losses": 0})
        log_to_file(username, "начал игру 'Кубик'")  # Записываем лог в файл
        await query.edit_message_text(
            f"Статистика (Кубик):\nПобед - {stats['wins']}\nПоражений - {stats['losses']}\n\nЯ бросил кубик. Какое число выпало? Выбери:",
            reply_markup=dice_keyboard()
        )
        return

    if query.data == "flip_coin":
        # Если пользователь выбрал "Орёл или решка", начинаем игру
        coin_result = random.choice(["eagle", "tails"])  # Орёл или решка
        stats = coin_stats.get(user_id, {"wins": 0, "losses": 0})
        log_to_file(username, "начал игру 'Орёл или решка'")  # Записываем лог в файл
        await query.edit_message_text(
            f"Статистика (Орёл/Решка):\nПобед - {stats['wins']}\nПоражений - {stats['losses']}\n\nЯ подбросил монетку. Что выпало? Выбери:",
            reply_markup=coin_keyboard()
        )
        context.user_data["coin_result"] = coin_result  # Сохраняем результат подбрасывания монетки
        return

    if query.data == "dice_stats":
        # Если пользователь выбрал статистику для игры "Кубик"
        stats = dice_stats.get(user_id, {"wins": 0, "losses": 0})
        await query.edit_message_text(
            f"Статистика (Кубик):\nПобед - {stats['wins']}\nПоражений - {stats['losses']}",
            reply_markup=dice_menu_keyboard(user_id)
        )
        return

    if query.data == "coin_stats":
        # Если пользователь выбрал статистику для игры "Орёл или решка"
        stats = coin_stats.get(user_id, {"wins": 0, "losses": 0})
        await query.edit_message_text(
            f"Статистика (Орёл/Решка):\nПобед - {stats['wins']}\nПоражений - {stats['losses']}",
            reply_markup=coin_menu_keyboard(user_id)
        )
        return

    if query.data == "back_to_main":
        # Если пользователь выбрал "Назад", возвращаемся в главное меню
        await query.edit_message_text("Выбери действие:", reply_markup=main_menu_keyboard())
        return

    if query.data.startswith("guess_"):
        # Обрабатываем выбор числа для игры "Кубик"
        user_choice = int(query.data.split("_")[1])

        if user_id not in user_numbers:
            await query.edit_message_text("Игра уже закончена. Начните новую игру.")
            return

        number_to_guess = user_numbers[user_id]

        if user_choice == number_to_guess:
            message = f"Поздравляю! Ты угадал число {number_to_guess}!"
            dice_stats.setdefault(user_id, {"wins": 0, "losses": 0})["wins"] += 1  # Увеличиваем счетчик побед
        else:
            message = f"К сожалению, ты не угадал. На кубике выпало число {number_to_guess}."
            dice_stats.setdefault(user_id, {"wins": 0, "losses": 0})["losses"] += 1  # Увеличиваем счетчик поражений

        # Возвращаемся в меню игры "Кубик"
        await query.edit_message_text(message, reply_markup=dice_menu_keyboard(user_id))

        # Удаляем число после окончания игры
        del user_numbers[user_id]
        return

    if query.data in ["coin_eagle", "coin_tails"]:
        # Обрабатываем выбор для игры "Орёл или решка"
        user_choice = query.data.split("_")[1]  # eagle или tails
        coin_result = context.user_data.get("coin_result")

        if coin_result == user_choice:
            result_text = "Орёл" if user_choice == "eagle" else "Решка"
            message = f"Поздравляю! Ты угадал {result_text}!"
            coin_stats.setdefault(user_id, {"wins": 0, "losses": 0})["wins"] += 1  # Увеличиваем счетчик побед
        else:
            result_text = "Орёл" if coin_result == "eagle" else "Решка"
            message = f"К сожалению, ты не угадал. Выпало {result_text}."
            coin_stats.setdefault(user_id, {"wins": 0, "losses": 0})["losses"] += 1  # Увеличиваем счетчик поражений

        # Возвращаемся в меню игры "Орёл или решка"
        await query.edit_message_text(message, reply_markup=coin_menu_keyboard(user_id))
        return

    if query.data == "tic_tac_toe":
        # Начинаем игру "Крестики-нолики"
        game_state = [""] * 9  # Пустое игровое поле
        tic_tac_toe_games[user_id] = {
            "state": game_state,
            "player_turn": True  # Первый ход делает игрок
        }
        log_to_file(username, "начал игру 'Крестики-нолики'")  # Записываем лог в файл
        await query.edit_message_text(
            "Добро пожаловать в игру 'Крестики-нолики'! Твой ход первый. Выбери ячейку:",
            reply_markup=create_tic_tac_toe_keyboard(game_state)
        )
        return

    if query.data.startswith("ttt_move_"):
        # Обрабатываем ход игрока в "Крестики-нолики"
        cell_index = int(query.data.split("_")[2])
        game_data = tic_tac_toe_games.get(user_id)

        if not game_data or game_data["state"][cell_index] != "":
            await query.answer("Эта ячейка уже занята!")
            return

        # Ход игрока
        game_data["state"][cell_index] = "X"
        game_data["player_turn"] = False

        # Проверяем победителя
        winner = check_winner(game_data["state"])
        if winner == "X":
            await query.edit_message_text("Поздравляю! Ты выиграл!", reply_markup=tic_tac_toe_menu_keyboard(user_id))
            tic_tac_toe_stats.setdefault(user_id, {"wins": 0, "losses": 0, "draws": 0})["wins"] += 1
            del tic_tac_toe_games[user_id]
            return
        elif winner == "draw":
            await query.edit_message_text("Ничья!", reply_markup=tic_tac_toe_menu_keyboard(user_id))
            tic_tac_toe_stats.setdefault(user_id, {"wins": 0, "losses": 0, "draws": 0})["draws"] += 1
            del tic_tac_toe_games[user_id]
            return

        # Ход бота
        bot_cell = bot_move(game_data["state"])
        game_data["state"][bot_cell] = "O"
        game_data["player_turn"] = True

        # Проверяем победителя после хода бота
        winner = check_winner(game_data["state"])
        if winner == "O":
            await query.edit_message_text("К сожалению, ты проиграл!", reply_markup=tic_tac_toe_menu_keyboard(user_id))
            tic_tac_toe_stats.setdefault(user_id, {"wins": 0, "losses": 0, "draws": 0})["losses"] += 1
            del tic_tac_toe_games[user_id]
            return
        elif winner == "draw":
            await query.edit_message_text("Ничья!", reply_markup=tic_tac_toe_menu_keyboard(user_id))
            tic_tac_toe_stats.setdefault(user_id, {"wins": 0, "losses": 0, "draws": 0})["draws"] += 1
            del tic_tac_toe_games[user_id]
            return

        # Обновляем игровое поле
        await query.edit_message_text(
            "Твой ход:",
            reply_markup=create_tic_tac_toe_keyboard(game_data["state"])
        )

    if query.data == "tic_tac_toe_stats":
        # Просмотр статистики для "Крестики-нолики"
        stats = tic_tac_toe_stats.get(user_id, {"wins": 0, "losses": 0, "draws": 0})
        await query.edit_message_text(
            f"Статистика (Крестики-нолики):\nПобед - {stats['wins']}, Поражений - {stats['losses']}, Ничьих - {stats['draws']}",
            reply_markup=tic_tac_toe_menu_keyboard(user_id)
        )
        return

    if query.data == "multiplication_table":
        # Начинаем игру "Таблица умножения"
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        multiplication_games[user_id] = {"num1": num1, "num2": num2}
        log_to_file(username, "начал игру 'Таблица умножения'")  # Записываем лог в файл
        await query.edit_message_text(
            f"Сколько будет {num1} × {num2}?",
            reply_markup=create_multiplication_keyboard(multiplication_games[user_id])
        )
        return

    if query.data.startswith("mult_answer_"):
        # Обрабатываем ответ пользователя в "Таблице умножения"
        user_answer = int(query.data.split("_")[2])
        game_data = multiplication_games.get(user_id)

        if not game_data:
            await query.answer("Игра уже завершена!")
            return

        correct_answer = game_data["num1"] * game_data["num2"]

        if user_answer == correct_answer:
            message = "Правильно! Ты молодец!"
            multiplication_stats.setdefault(user_id, {"wins": 0, "losses": 0})["wins"] += 1
        else:
            message = f"К сожалению, это неверно. Правильный ответ: {correct_answer}."
            multiplication_stats.setdefault(user_id, {"wins": 0, "losses": 0})["losses"] += 1

        # Удаляем текущую игру и возвращаемся в меню
        del multiplication_games[user_id]
        await query.edit_message_text(message, reply_markup=multiplication_menu_keyboard(user_id))

    if query.data == "multiplication_stats":
        # Просмотр статистики для "Таблица умножения"
        stats = multiplication_stats.get(user_id, {"wins": 0, "losses": 0})
        await query.edit_message_text(
            f"Статистика (Таблица умножения):\nПобед - {stats['wins']}, Поражений - {stats['losses']}",
            reply_markup=multiplication_menu_keyboard(user_id)
        )
        return

def main() -> None:
    """Основная функция для запуска бота"""
    # Замените 'YOUR_TOKEN' на ваш токен бота
    application = Application.builder().token("YOUR_TOKEN").build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_game))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()
