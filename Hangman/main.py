import sys
from collections import Counter
from random import choice, sample
from typing import TypedDict

from display import draw_hangman, print_separator, win_pics

EASY_MODE_LETTERS: int = 2
WORDS: list[str] = []


class GameState(TypedDict):
    word: str
    mask: list[str]
    error_count: int
    guessed_letters: list[str]
    max_errors: int
    game_mode: str


def main() -> None:
    """Главный цикл приложения, его задача — управлять игрой и обрабатывать исключения."""

    try:
        load_words()
    except FileNotFoundError:
        print("Ошибка: файл со словами 'words.txt' не найден. Программа завершается.")
        sys.exit(1)
    except ValueError as e:
        print(f"Ошибка в файле со словами: {e}. Программа завершается.")
        sys.exit(1)
    except Exception as e:
        print(f"Непредвиденная ошибка при загрузке слов: {e}")
        sys.exit(1)

    try:
        while True:
            game_mode = show_menu()

            if game_mode == "exit":
                print("Возвращайтесь скорее, игре без вас будет скучно!")
                break

            try:
                start_game(game_mode=game_mode)
            except RuntimeError as e:
                print(f"Произошла ошибка во время игры: {e}")
                print("Возвращаемся в главное меню...")

    except KeyboardInterrupt:
        print("\nИгра прервана пользователем. До встречи!")
        sys.exit(0)


def show_menu() -> str:
    """
    Отображает главное меню игры и обрабатывает выбор пользователя.

    Предлагает пользователю выбрать между лёгким режимом, нормальным режимом или выходом.
    Повторяет запрос, пока не будет получен корректный ввод.

    :return: Режим игры ('easy', 'normal' или 'exit'), выбранный пользователем.
    """
    actions = {
        1: ("Да, в легком режиме (изначально известны 2 буквы)", "easy"),
        2: ("Да, в нормальном режиме (все буквы неизвестны)", "normal"),
        3: ("Нет", "exit"),
    }
    menu_text = "\n".join(f"[{num}] {desc}" for num, (desc, _) in actions.items())
    valid_choices = set(actions.keys())

    while True:
        print('Добро пожаловать в игру "Виселица"!\nХотите начать новую игру?\n')
        print(menu_text)
        choice_str = input("Введите цифру: ")
        try:
            user_choice = int(choice_str)  # переименовали переменную
            if user_choice in valid_choices:
                return actions[user_choice][1]  # возвращаем режим
            else:
                print(f"Пожалуйста, введите один из вариантов: {', '.join(map(str, valid_choices))}")
        except ValueError:
            print(f"Ошибка: введите цифру из предложенных вариантов: {', '.join(map(str, valid_choices))}!")


def start_game(game_mode: str = "normal") -> None:
    """
    Запускает игру в указанном режиме.

    :param game_mode: Режим игры, может быть "easy" или "normal". По умолчанию "normal".
    """
    state: GameState = initialize_game(game_mode=game_mode)
    play_round(state)


def initialize_game(game_mode: str = "normal") -> GameState:
    """
    Инициализирует состояние игры.

    :param game_mode: Режим игры, может быть "easy" или "normal". По умолчанию "normal".
    :return: Словарь с состоянием игры, содержащий загаданное слово, маску слова, счетчик ошибок, список угаданных букв,
    максимальное количество ошибок и режим игры.
    """
    word = get_random_word()
    word = word.upper()
    mask: list[str] = create_word_mask(word)

    state: GameState = {
        "word": word,
        "mask": mask,
        "error_count": 0,
        "guessed_letters": [],
        "max_errors": 6,
        "game_mode": game_mode,
    }

    if game_mode == "easy":
        letters_to_reveal: list[str] = select_letters_for_easy(word)
        if not letters_to_reveal:
            print("Нет подходящих слов для лёгкого режима. Игра начинается в нормальном режиме.")
            state["game_mode"] = "normal"
        else:
            for letter in letters_to_reveal:
                reveal_letter(state, letter)
                state["guessed_letters"].append(letter)

    return state


def play_round(state: GameState) -> None:
    """
    Основной игровой цикл, в котором игрок угадывает буквы до тех пор, пока не отгадает слово или не исчерпает
    все попытки.

    :param state: Текущее состояние игры.
    """
    print_separator()
    print("Игра началась! Укажите букву, которая, по-вашему, есть в загаданном слове")
    while state["error_count"] < state["max_errors"] and "_" in state["mask"]:
        process_player_turn(state)
    check_game_end(state)


def process_player_turn(state: GameState) -> None:
    """
    Обрабатывает ход игрока: принимает ввод буквы, проверяет ее и обновляет состояние игры.

    :param state: Текущее состояние игры.
    """
    display_game_state(state)
    player_letter: str = input("Ваша буква (только одна, кириллица): ").upper()
    print_separator()

    if not is_valid_russian_letter(player_letter):
        print(
            "Некорректный ввод. Разрешается вводить только одну букву кириллического алфавита.\n"
            "Пожалуйста, попробуйте снова."
        )
        return

    if player_letter in state["guessed_letters"]:
        print("Вы уже вводили эту букву, введите другую!")
        return

    update_word_mask(state, player_letter)


def display_game_state(state: GameState) -> None:
    """
    Отображает текущее состояние игры: виселицу, маску слова, оставшиеся попытки и использованные буквы.

    :param state: Текущее состояние игры.
    """
    print_separator()
    print(
        f"{draw_hangman(state['error_count'])}\n"
        f"Загаданное слово: {' '.join(state['mask'])}\n"
        f"Осталось попыток: {state['max_errors'] - state['error_count']}\n"
        f"Использованные буквы: {', '.join(sorted(state['guessed_letters']))}\n"
    )


def select_letters_for_easy(word: str) -> list[str]:
    """
    Выбирает буквы для раскрытия в легком режиме.

    :param word: Загаданное слово.
    :return: Список букв, которые будут раскрыты.
    """
    letter_counts: dict[str, int] = Counter(word)
    single_occurrence_letters: list[str] = [char for char, count in letter_counts.items() if count == 1]

    if len(single_occurrence_letters) >= EASY_MODE_LETTERS:
        return sample(single_occurrence_letters, EASY_MODE_LETTERS)
    return []


def is_valid_russian_letter(char: str) -> bool:
    """
    Проверяет, является ли введенный символ одной буквой русского алфавита.

    :param char: Введенный символ.
    :return: True, если символ является одной буквой русского алфавита, иначе False.
    """
    return len(char) == 1 and char.isalpha() and ("А" <= char <= "Я" or char == "Ё")


def check_game_end(state: GameState) -> None:
    """
    Проверяет, закончилась ли игра, и выводит сообщение о победе или поражении.

    :param state: Текущее состояние игры.
    """
    if state["error_count"] >= state["max_errors"]:
        print(
            f"Вы потратили все попытки и проиграли!\nБыло загадано слово: {state['word']}\n"
            f"{draw_hangman(state['error_count'])}"
        )
    else:
        print(f"Поздравляем, вы верно отгадали слово {state['word']}\n{win_pics}")
    print_separator()


def update_word_mask(state: GameState, letter: str) -> None:
    """
    Обновляет маску слова, если угаданная буква есть в слове, иначе увеличивает счетчик ошибок.

    :param state: Текущее состояние игры.
    :param letter: Угаданная буква.
    """
    state["guessed_letters"].append(letter)
    if letter in state["word"]:
        print(f"Верно, буква {letter} есть в загаданном слове!")
        reveal_letter(state, letter)
    else:
        print(f"К сожалению, буква {letter} отсутствует в загаданном слове.")
        state["error_count"] += 1


def reveal_letter(state: GameState, letter: str) -> None:
    """
    Раскрывает букву в маске слова, если она есть в загаданном слове.

    :param state: Текущее состояние игры.
    :param letter: Буква, которую нужно раскрыть.
    """
    for i in range(len(state["word"])):
        if state["word"][i] == letter:
            state["mask"][i] = letter


def load_words() -> None:
    """
    Загружает список слов из файла в глобальную переменную WORDS.
    """
    global WORDS
    with open("words.txt", encoding="utf-8") as file:
        WORDS = file.read().splitlines()
        if not WORDS:
            raise ValueError("Файл слов пустой.")


def get_random_word() -> str:
    """
    Выбирает случайное слово из файла для игры.

    :return: Случайное слово.
    """
    if not WORDS:
        raise RuntimeError("Список слов пуст.")
    return choice(WORDS)


def create_word_mask(word: str) -> list[str]:
    """
    Создает маску для загаданного слова, состоящую из подчеркиваний.

    :param word: Загаданное слово.
    :return: Список подчеркиваний, соответствующий длине слова.
    """
    return ["_" for _ in word]


if __name__ == "__main__":
    main()