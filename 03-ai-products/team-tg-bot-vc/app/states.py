from aiogram.fsm.state import State, StatesGroup


class TaskStates(StatesGroup):
    """Состояния для работы с задачами."""
    
    waiting_for_task_text = State()  # Ожидание ввода текста задачи
