from aiogram.fsm.state import State, StatesGroup


class CarInfo(StatesGroup):
    waiting_for_car_brand = State()
    waiting_for_motor_model = State()
    msg_or_photo_breaking = State()
