import asyncio
from pprint import pprint
from time import time
import aiohttp
import json
from typing import Union
from pyrogram.errors import UserNotParticipant
from bot.utils.scripts import escape_html

from bot.config import settings
# from bot.utils.scripts import escape_html
from bot.utils.logger import *

b_name = {
    "b_01": "TapFlix",
    "b_02": "Monument to Toncoin",
    "b_03": "Factory",
    "b_04": "Tapping Guru",
    "b_05": "To the moon!",
    "b_06": "Trampoline",
    "b_07": "Bit Club",
    "b_08": "Karaoke",
    "b_09": "Point of view",
    "b_10": "Prosecco fountain",
    "b_11": "Biker club",
    "b_12": "Istukan",
    "b_13": "Salmon",
    "b_14": "Telegram duck",
    "b_15": "Brewery",
    "b_16": "Webrave",
    "b_17": "Gold button",
    "b_18": "Casino",
    "b_19": "Cooking hub",
    "b_20": "Tap stadium",
}

async def update_build(http_client: aiohttp.ClientSession, b_id: str) -> Union[str, dict]:
    response_text = ""
    try:
        # Вызов синхронного метода через asyncio.to_thread
        response = await asyncio.to_thread(http_client.post, url="https://api.tapswap.club/api/town/upgrade_building", json={"building_id": b_id})

        if response is None:
            logger.error("Received None response during building update")
            return "None response"

        response_text = response.text

        if not response_text:
            logger.error("Received empty response text during building update")
            return "Empty response"

        response.raise_for_status()

        # Парсим текст как JSON
        message = json.loads(response_text)

        if message is None:
            logger.error("Failed to parse response text as JSON during building update")
            return "Invalid JSON response"

        return message  # возвращаем инфу об обновлении здания

    except Exception as error:
        logger.error(f"Error during update building: {escape_html(error)} | Response text: {escape_html(response_text)}")
        await asyncio.sleep(delay=3)
        return str(error)


async def build_town(self, http_client: aiohttp.ClientSession, profile_data) -> bool:
    global b_name

    print(f"profile_data: {profile_data}")  # Логирование для проверки данных
    logger.info(f"{self.session_name} | build_town function started")

    # Текущие ресурсы
    b_crystals = profile_data["player"].get("crystals", 0)
    b_blocks = profile_data["player"].get("blocks", 0)
    b_videos = profile_data["player"].get("videos", 0)
    b_reward = profile_data["player"]["stat"].get("reward", 0)

    logger.info(f"{self.session_name} | Resources loaded: crystals={b_crystals}, blocks={b_blocks}, videos={b_videos}, reward={b_reward}")

    upgrade_list = dict()

    # Создаем словарь зданий возможных к апгрейду с указанием уровня {id: [lvl, rate]}
    for id, name in b_name.items():
        logger.info(f"{self.session_name} | Checking building {name} with id {id}")
        cost = build_new_level(id, profile_data)

        if cost is None:
            logger.warning(f"{self.session_name} | Skipping {name} due to missing cost")
            continue

        cur_lvl = build_current_level(id, profile_data)
        logger.info(f"{self.session_name} | Current level for {name} is {cur_lvl}")

        # Проверим, строится ли здание
        is_construct = False
        for data in profile_data["player"]["town"]["buildings"]:
            if data['id'] == id and data["ready_at"] / 1000 > time():
                is_construct = True
                logger.info(f"{self.session_name} | {name} is currently under construction")
                break
        if is_construct:
            continue

        # Проверим достижение максимального уровня
        if cur_lvl >= settings.MAX_TOWN_LEVEL:
            logger.info(f"{self.session_name} | {name} reached maximum level")
            continue

        r_name = r_lvl = None
        if (
                cost["shares"] <= b_reward
                and cost["blocks"] <= b_blocks
                and cost["videos"] <= b_videos
        ):
            if cost.get("r_id") is not None:
                r_name = b_name.get(cost["r_id"], "Unknown")
                r_lvl = cost.get("r_level", 0)
                if r_lvl <= build_current_level(cost["r_id"], profile_data):
                    upgrade_list[id] = [cur_lvl]
                    upgrade_list[id].append(cost["rate"])
                else:
                    logger.info(f"{self.session_name} | Required building {r_name} level too low")
                    continue
            else:
                upgrade_list[id] = [cur_lvl]
                upgrade_list[id].append(cost["rate"])

            logger.info(
                f"{self.session_name} | Build {name} [lvl: {cur_lvl}] available for upgrade. "
                f"Cost: {cost['shares']} coins, {cost['blocks']} blocks, {cost['videos']} videos. Required: {r_name}[lvl: {r_lvl}]"
            )

    # Выбираем лучшее здание для апгрейда
    while True:
        await_time = builders_free(self, profile_data)
        if await_time > 0:
            logger.info(f"{self.session_name} | Waiting for free builder ({await_time}s)")
            return False

        id_best = ""
        lvl_min = 100

        # Если список зданий для апгрейда пуст
        if not upgrade_list:
            logger.info(f"{self.session_name} | No buildings available for upgrade")
            return False

        for id, res in upgrade_list.items():
            if lvl_min > res[0]:
                id_best = id
                lvl_min = res[0]

        if not id_best:
            logger.info(f"{self.session_name} | No more upgrades available")
            break

        logger.success(f"{self.session_name} | Starting upgrade of {b_name[id_best]} to level {lvl_min + 1}")

        # Логируем начало update_build
        logger.info(f"{self.session_name} | Sending upgrade request for {b_name[id_best]}")
        status = await update_build(http_client=http_client, b_id=id_best)

        if status is None:
            logger.error(f"{self.session_name} | Received None as status from update_build")
            await asyncio.sleep(delay=5)
            return False
        
        if isinstance(status, dict) and "player" in status:
            logger.info(f"{self.session_name} | Successfully upgraded {b_name[id_best]}, updating profile data")
            # Обновляем профиль, если есть ключ "player"
            profile_data.update(status)
            del upgrade_list[id_best]
            await asyncio.sleep(delay=15)
            return True

        # Логируем различные сценарии обработки статусов
        if status == "building_already_upgrading":
            logger.warning(f"{self.session_name} | Building {b_name[id_best]} is already upgrading. Sleeping 15s")
            await asyncio.sleep(delay=15)
            return True
        elif status == "no_available_builders":
            logger.warning(f"{self.session_name} | No available builders for {b_name[id_best]}. Sleeping 15s")
            await asyncio.sleep(delay=15)
            return False
        elif status == "required_building_level_too_low":
            logger.warning(f"{self.session_name} | Required building level for {b_name[id_best]} too low. Sleeping 15s")
            await asyncio.sleep(delay=15)
            return False
        elif status == "not_enough_videos":
            logger.warning(f"{self.session_name} | Not enough videos to upgrade {b_name[id_best]}. Sleeping 15s")
            await asyncio.sleep(delay=15)
            return False
        elif status == "not_enough_shares":
            logger.warning(f"{self.session_name} | Not enough coins to upgrade {b_name[id_best]}. Sleeping 15s")
            await asyncio.sleep(delay=15)
            return False
        elif status == "Unauthorized":
            logger.warning(f"{self.session_name} | Unauthorized to upgrade {b_name[id_best]}. Stopping process")
            await asyncio.sleep(delay=5)
            return False
        elif status == "tg_channel_check_failed":
            logger.warning(f"{self.session_name} | TG channel check failed for {b_name[id_best]}. Retrying subscription tasks")
            await asyncio.sleep(delay=5)
            await subscribe_channel_task(self)
            await social_channel_task(self, http_client)
            return False
        else:
            logger.error(f"{self.session_name} | Unknown error during upgrade: {status}")
            await asyncio.sleep(delay=5)
            break

    logger.info(f"{self.session_name} | build_town function completed")
    return False


# Функция возвращает перечень ресурсов для апдейта
# Функция возвращает перечень ресурсов для апдейта
def build_new_level(b_id, profile_data) -> Union[dict, None]:
    data = {"id": b_id}

    i = int(b_id.removeprefix("b_")) - 1  # вычислим индекс из id здания

    building_data = profile_data["conf"]["town"]["buildings"][i]
    if isinstance(building_data, dict):  # Проверка на словарь
        levels = building_data.get("levels")
        if isinstance(levels, list):  # Если levels — это список, берем нужный элемент по индексу
            if len(levels) > 2:  # Проверяем, что индекс 2 существует
                level_data = levels[2]
            else:
                logger.error(f"Levels list for building {b_id} is too short")
                return None
        elif isinstance(levels, dict):  # Если levels — это словарь, как предполагалось ранее
            level_data = levels.get(2)
        else:
            logger.error(f"Expected dict or list for levels but got {type(levels)}")
            return None
    else:
        logger.error(f"Expected dict for building data but got {type(building_data)}")
        return None

    if level_data is None:
        return None

    data.update(level_data.get("cost", {}))

    # добыча блоков на новом уровне шт/час
    data["rate"] = int(level_data.get("rate", 0) * 3600)
    req = level_data.get("required")  # требование наличие уровня другого здания
    if req:
        data["r_id"] = req.get("id")
        data["r_level"] = req.get("level")
    else:
        data["r_id"] = None
        data["r_level"] = None

    return data


# Функция возвращает текущий уровень здания по его id
def build_current_level(b_id, profile_data) -> int:
    for data in profile_data.get("player", {}).get("town", {}).get("buildings", []):
        if b_id == data.get("id"):
            # Проверка, что уровень уже построен, если нет — понижаем
            ready_at = data.get("ready_at", 0) / 1000
            if isinstance(data, dict) and ready_at > time():
                return data.get("level", 0) - 1
            else:
                return data.get("level", 0)
    return 0


# Функция возвращает минимально время освобождения строителя
# Вызывать лучше всего после обновления challenge
# Возвращает 0 если хотя бы есть один свободный
def builders_free(self, profile_data) -> int:
    global b_name

    await_time = 0
    player_time = profile_data.get("player", {}).get("time", 0)
    builds_stat = profile_data.get("player", {}).get("town", {}).get("buildings", [])
    count_builders = 0

    for build in builds_stat:
        # Время ожидания до окончания стройки
        time_at = build.get("ready_at", 0) - player_time
        if time_at > 0:
            count_builders += 1

            if await_time == 0:
                await_time = time_at
            elif await_time > time_at:
                await_time = time_at

            logger.info(
                f"{self.session_name} | "
                f"Build <y>{b_name.get(build.get('id'), 'Unknown')}</y> "
                f"wait <c>{int(time_at / 1000):,}</c> sec..."
            )

            # Заняты все строители, вернем время освобождения первого
            if count_builders >= profile_data.get("player", {}).get("town", {}).get("builders", 0):
                logger.warning(
                    f"{self.session_name} | <r>All the builders are busy...</r>"
                )
                return int(await_time / 1000)

    logger.success(f"{self.session_name} | <lg>Excellent, there is a free builder!</lg>")

    return 0


# Подписка на каналы
async def subscribe_channel_task(self):
    async with self.tg_client:
        self.user_id = (await self.tg_client.get_me()).id
        await asyncio.sleep(delay=5)

        channels_id = ["tapswapai"]

        for channel_id in channels_id:
            try:
                member = await self.tg_client.get_chat_member(channel_id, self.user_id)
                if member.status not in ["member", "administrator", "creator"]:
                    await self.tg_client.join_chat(channel_id)

                    logger.info(f"{self.tg_client.name} | You are already subscribed to the channel @{channel_id}")
                    await asyncio.sleep(delay=5)
            except UserNotParticipant:
                await self.tg_client.join_chat(channel_id)

                logger.info(f"{self.tg_client.name} | Subscribe channel @{channel_id} for task")
                await asyncio.sleep(delay=5)


async def social_channel_task(self, http_client):
    finish_mission_item = int(await self.finish_mission_item(self, http_client, "M0", "check", 0))
    await asyncio.sleep(delay=5)

    finish_mission_item += await self.finish_mission_item(self, http_client, "M0", "check", 1)
    await asyncio.sleep(delay=5)

    finish_mission_item += await self.finish_mission_item(self, http_client, "M0", "check", 2)
    await asyncio.sleep(delay=5)

    finish_mission = await self.finish_mission(self, http_client, "M0")
    await asyncio.sleep(delay=5)

    if finish_mission and finish_mission_item == 3:
        await self.claim_reward(self, http_client, "M0")
