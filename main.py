import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import os
import re
import random

try:
    TOKEN = os.environ['API_KEY']
    GROUP_ID = os.environ['GROUP_ID']
except RuntimeError:
    print("Не заданы VK_TOKEN или VK_GROUP_ID в .env")

DICE_PATTERN = re.compile(r'(\d*)d(\d+)([+-]\d+)?', re.IGNORECASE)



def parse_dice_and_description(body):
    """
    Ищет кубик в строке. Возвращает (dice_str, num_dice, die_sides, modifier, description).
    Если кубик не найден — возвращает (None, 1, 20, 0, body).
    """
    body = body.strip()
    if not body:
        return None, 1, 20, 0, ""
    match = DICE_PATTERN.search(body)
    if not match:
        return None, 1, 20, 0, body

    num_dice = int(match.group(1)) if match.group(1) else 1
    die_sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0
    dice_str = match.group(0).lower()

    description = (body[:match.start()] + " " + body[match.end():]).strip()
    description = re.sub(r'\s+', ' ', description)  # убираем двойные пробелы

    return dice_str, num_dice, die_sides, modifier, description


def roll_dice(num_dice, die_sides, modifier):
    """Бросает кубики, возвращает (total, rolls)."""
    if num_dice < 1 or num_dice > 100:
        return None
    if die_sides < 2 or die_sides > 1000:
        return None

    rolls = [random.randint(1, die_sides) for _ in range(num_dice)]
    total = sum(rolls) + modifier
    return total, rolls


def format_result(rolls, die_sides, modifier, total):
    """Форматирует результат броска."""
    if len(rolls) == 1 and modifier == 0:
        value = rolls[0]
        if die_sides == 20 and value == 20:
            return f"🎲 d20: {value} 🎉 УРА ПОБЕДА!"
        if die_sides == 20 and value == 1:
            return f"🎲 d20: {value} 💀 ВЫ ПРОИГРАЛИ"
        return f"🎲 d{die_sides}: {value}"

    detail = " + ".join(str(r) for r in rolls)
    if modifier != 0:
        detail += f" {'+' if modifier > 0 else '-'} {abs(modifier)}"
    return f"🎲 {detail} = {total}"


def get_user_name(vk, user_id):
    try:
        user_info = vk.users.get(user_ids=user_id)[0]
        return f"{user_info['first_name']} {user_info['last_name']}"
    except Exception:
        return "Игрок"


def main():
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)

    print("Бот запущен и слушает сообщения...")

    for event in longpoll.listen():
        if event.type != VkBotEventType.MESSAGE_NEW:
            continue

        msg_text = event.obj.message.get('text', '').strip()
        peer_id = event.obj.message['peer_id']
        user_id = event.obj.message['from_id']

        # Команда: /к или /r
        if not (msg_text.startswith('/к') or msg_text.startswith('/r')):
            continue

        body = msg_text[2:].strip()

        dice_str, num_dice, die_sides, modifier, description = parse_dice_and_description(body)

        if dice_str is None:
            dice_str = f"{num_dice}d{die_sides}" if num_dice > 1 else f"d{die_sides}"
            if modifier:
                dice_str += f"{'+' if modifier > 0 else ''}{modifier}"

        result = roll_dice(num_dice, die_sides, modifier)
        if result is None:
            vk.messages.send(
                peer_id=peer_id,
                message=f"🎲 Неверные параметры кубика. Пример: 2d20, d20+5, 3d6",
                random_id=random.randint(0, 2 ** 31),
            )
            continue

        total, rolls = result
        result_text = format_result(rolls, die_sides, modifier, total)

        user_name = get_user_name(vk, user_id)

        header = f"[id{user_id}|{user_name}] бросает {dice_str} по причине: "
        if description:
            header += f" -- {description}"

        full_message = f"{header}\n{result_text}"

        vk.messages.send(
            peer_id=peer_id,
            message=full_message,
            random_id=random.randint(0, 2 ** 31),
        )



if __name__ == '__main__':
    main()