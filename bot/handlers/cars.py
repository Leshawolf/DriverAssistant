import logging
import io
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from bot.state.car_info import CarInfo
from bot.services.openrouter_client import client, ask_llm_with_image, ask_llm_with_text
import re

logger = logging.getLogger(__name__)
router = Router(name=__name__)


_heading_re = re.compile(r"^#+\s*(.*)$", flags=re.MULTILINE)  # ### Заголовок
_asterisk_re = re.compile(r"\*+")  # любые * или **


def md_headings_to_html(text: str) -> str:
    text = _heading_re.sub(r"<b>\1</b>", text)  # заголовки → <b>
    text = _asterisk_re.sub("", text)  # удаляем все *
    return text


WELCOME_TEXT = (
    "<b>🚘 Привет! Я — AI-ассистент, помогающий разбираться с поломками автомобилей.</b>\n\n"
    "Чтобы начать, напиши, пожалуйста, <b>марку твоей машины</b> — например: "
    "<i>BMW</i>, <i>LADA</i>, <i>Toyota</i>, <i>Kia</i> и т.д.\n\n"
    "Это поможет мне точнее подобрать возможные причины неисправностей, "
    "когда ты опишешь проблему или пришлёшь фото.\n\n"
    "<b>Жду марку автомобиля!</b> 🛠️"
)


@router.message(Command("start"))
async def cmd_start(msg: types.Message, state: FSMContext) -> None:
    await msg.answer(WELCOME_TEXT)
    await state.set_state(CarInfo.waiting_for_car_brand)
    logger.debug("FSM: user %s -> waiting_for_car_brand", msg.from_user.id)


@router.message(CarInfo.waiting_for_car_brand)
async def handle_car_brand(msg: types.Message, state: FSMContext) -> None:
    brand = msg.text.strip()
    logger.info("Received car brand '%s' from user id=%s", brand, msg.from_user.id)

    await state.update_data(car_brand=brand)
    logger.debug("FSM: saved car_brand for user %s", msg.from_user.id)

    await msg.answer(
        f"Спасибо! Я запомнил: <b>{brand}</b>.\n"
        "Теперь напишите, пожалуйста, <b>модель вашего двигателя</b>."
    )
    await state.set_state(CarInfo.waiting_for_motor_model)


@router.message(CarInfo.waiting_for_motor_model)
async def handle_motor_model(msg: types.Message, state: FSMContext) -> None:
    model = msg.text.strip()
    logger.info("Received motor model '%s' from user id=%s", model, msg.from_user.id)

    await state.update_data(motor_model=model)
    logger.debug("FSM: saved motor_model for user %s", msg.from_user.id)

    data = await state.get_data()
    brand_saved = data["car_brand"]

    await msg.answer(
        f"Отлично! С вами приятно работать.\n"
        f"Марка: <b>{brand_saved}</b>\n"
        f"Мотор: <b>{model}</b>\n\n"
        "Теперь опишите проблему или пришлите фото неисправности."
    )
    await state.set_state(CarInfo.msg_or_photo_breaking)


@router.message(CarInfo.msg_or_photo_breaking)
async def handle_problem_input(msg: types.Message, state: FSMContext) -> None:
    """Обрабатываем описание неисправности в одном из трёх форматов."""

    # 1. достаем марку и мотор
    data = await state.get_data()
    brand = data.get("car_brand", "unknown brand")
    motor = data.get("motor_model", "unknown motor")

    # 2. определяем вид ввода
    image_bytes: bytes | None = None
    user_text = ""

    if msg.photo:  # фото есть
        # скачиваем наибольшее фото
        largest_photo: types.PhotoSize = msg.photo[-1]
        file = await msg.bot.get_file(largest_photo.file_id)
        buffer = io.BytesIO()
        await msg.bot.download_file(file.file_path, buffer)
        buffer.seek(0)
        image_bytes = buffer.read()
        if msg.caption:
            user_text = msg.caption.strip()
        input_desc = "photo_with_caption" if user_text else "photo_only"
    else:  # чистый текст
        user_text = msg.text.strip() if msg.text else ""
        input_desc = "text_only"

    logger.info("User %s sent %s", msg.from_user.id, input_desc)

    # 3. формируем системный заголовок
    system_header = (
        f"Марка: {brand}. Двигатель: {motor}. "
        "Ниже описание проблемы пользователя. Дай 2–3 возможные причины и шаги диагностики."
    )
    prompt = f"{system_header}\n\n{user_text}"

    # 4. вызываем модель
    try:
        if image_bytes:
            answer = await ask_llm_with_image(image_bytes, prompt)
        else:
            answer = await ask_llm_with_text(prompt)
    except Exception as e:
        logger.error("LLM request failed: %s", e, exc_info=True)
        await msg.answer("⚠️ Произошла ошибка при обращении к LLM. Попробуйте позже.")
        return

    # 5. конвертируем markdown‑лайт → HTML и отвечаем
    html_answer = md_headings_to_html(answer)
    await msg.answer(html_answer)  # bot default parse_mode=HTML

    # 6. очищаем FSM
    await state.clear()
    logger.debug("FSM cleared for user %s", msg.from_user.id)
