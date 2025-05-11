from aiogram.fsm.state import State, StatesGroup

class OrderFSM(StatesGroup):
    name = State()
    phone = State()
    address = State()
    salt_type = State()
    quantity = State()
    payment = State()
    confirm = State()

