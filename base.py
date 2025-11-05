# base.py
import re
import bcrypt
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, ForeignKey, DateTime
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# ---- Конфігурація DB ----
DB_URL = "sqlite:///learning_app.db"
Base = declarative_base()
engine = create_engine(DB_URL, echo=False)
Session = sessionmaker(bind=engine)
session = Session()


# ---- Моделі ----
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="active")
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="tasks")
    steps = relationship("TaskStep", back_populates="task", cascade="all, delete-orphan")


class TaskStep(Base):
    __tablename__ = "task_steps"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    title = Column(String(200), nullable=False)
    is_done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    task = relationship("Task", back_populates="steps")


Base.metadata.create_all(engine)


# ---- Утиліти ----
def parse_deadline(date_str: str):
    """Приймає 'дд-мм-рррр', 'дд.мм.рррр' або 'дд мм рррр', повертає datetime(date) або None."""
    if not date_str or not date_str.strip():
        return None
    s = re.sub(r"[.\s-]+", "-", date_str.strip())

    parts = s.split("-")
    if len(parts) != 3:
        return None
    try:
        day, month, year = map(int, parts)
        return datetime(year, month, day, tzinfo=timezone.utc)
    except ValueError:
        return None


def format_deadline(dt):
    if not dt:
        return "—"
    return dt.astimezone(timezone.utc).strftime("%d.%m.%Y")


# ---- Аутентифікація ----
def register_user():
    print("\n=== Реєстрація користувача ===")
    username = input("Ім'я користувача: ").strip()
    email = input("Email: ").strip().lower()
    password = input("Пароль: ").strip()
    confirm = input("Повторіть пароль: ").strip()

    if not username or not email or not password:
        print("❌ Ім'я, email та пароль не можуть бути порожніми.")
        return None

    if password != confirm:
        print("❌ Паролі не співпадають.")
        return None

    if session.query(User).filter_by(username=username).first():
        print("❌ Ім'я вже зайняте.")
        return None
    if session.query(User).filter_by(email=email).first():
        print("❌ Email вже використовується.")
        return None

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(username=username, email=email, password_hash=hashed)
    session.add(user)
    session.commit()
    print(f"✅ Користувач '{username}' зареєстрований.")
    return user


def login_user():
    print("\n=== Вхід ===")
    username = input("Ім'я користувача: ").strip()
    password = input("Пароль: ").strip()
    user = session.query(User).filter_by(username=username).first()
    if not user:
        print("❌ Користувача не знайдено.")
        return None
    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        print("❌ Невірний пароль.")
        return None
    print(f"✅ Вітаємо, {user.username}!")
    return user


# ---- Робота із завданнями ----
def view_tasks(user: User):
    tasks = session.query(Task).filter_by(user_id=user.id).order_by(Task.created_at).all()
    if not tasks:
        print("📭 У вас немає завдань.")
        return
    for t in tasks:
        dl = format_deadline(t.deadline)
        overdue = ""
        if t.deadline and t.deadline < datetime.now():
            overdue = " ⚠️ Прострочено"
        print(f"\n[{t.id}] {t.title} — {t.status} | Дедлайн: {dl}{overdue}")
        if t.description:
            print(f"   Опис: {t.description}")
        if t.steps:
            print("   Кроки:")
            for s in t.steps:
                mark = "✅" if s.is_done else "⬜"
                print(f"     [{s.id}] {mark} {s.title}")


def add_task(user: User):
    print("\n=== Створення завдання ===")
    title = input("Назва: ").strip()
    description = input("Опис: ").strip()
    while True:
        dl_input = input("Дедлайн (дд-мм-рррр або дд.мм.рррр або дд мм рррр) або пусто: ").strip()
        if dl_input == "":
            dl = None
            break
        dl = parse_deadline(dl_input)
        if dl is None:
            print("❌ Невірний формат дати. Спробуйте ще раз.")
        else:
            break

    task = Task(title=title, description=description, deadline=dl, user=user)
    session.add(task)
    session.commit()
    print("✅ Завдання створено. Тепер можна додати кроки.")
    # додати кроки одразу
    while True:
        add = input("Додати крок? (y/n): ").strip().lower()
        if add == "y":
            step_title = input("Текст кроку: ").strip()
            if step_title:
                step = TaskStep(title=step_title, task=task)
                session.add(step)
                session.commit()
                print("   ➕ Крок додано.")
        else:
            break


def edit_task(user: User):
    view_tasks(user)
    try:
        tid = int(input("\nВведіть ID завдання для редагування: ").strip())
    except ValueError:
        print("❌ Невірний ID.")
        return
    task = session.query(Task).filter_by(id=tid, user_id=user.id).first()
    if not task:
        print("❌ Завдання не знайдено.")
        return

    print(f"\nРедагування [{task.id}] {task.title}")
    new_title = input(f"Нова назва (Enter - залишити '{task.title}'): ").strip()
    new_desc = input(f"Новий опис (Enter - залишити): ").strip()
    new_status = input(f"Новий статус (Enter - залишити '{task.status}'): ").strip()
    new_dl = input("Новий дедлайн (дд-мм-рррр) або пусто щоб залишити: ").strip()
    if new_title:
        task.title = new_title
    if new_desc:
        task.description = new_desc
    if new_status:
        task.status = new_status
    if new_dl:
        parsed = parse_deadline(new_dl)
        if parsed is None:
            print("⚠️ Невірний формат дедлайну — дедлайн не змінено.")
        else:
            task.deadline = parsed
    session.commit()
    print("✅ Зміни збережено.")
    # Перейти в редактор кроків
    edit_steps(task)


def edit_steps(task: Task):
    while True:
        print(f"\n--- Кроки для завдання [{task.id}] {task.title} ---")
        steps = session.query(TaskStep).filter_by(task_id=task.id).order_by(TaskStep.id).all()
        if not steps:
            print("(немає кроків)")
        else:
            for s in steps:
                mark = "✅" if s.is_done else "⬜"
                print(f"[{s.id}] {mark} {s.title}")
        print("\n1) Додати крок")
        print("2) Позначити/зняти позначку з кроку")
        print("3) Редагувати текст кроку")
        print("4) Видалити крок")
        print("5) Назад")
        choice = input("Оберіть дію: ").strip()
        if choice == "1":
            text = input("Текст кроку: ").strip()
            if text:
                new = TaskStep(title=text, task=task)
                session.add(new)
                session.commit()
                print("✅ Крок додано.")
        elif choice == "2":
            try:
                sid = int(input("ID кроку: ").strip())
                step = session.query(TaskStep).filter_by(id=sid, task_id=task.id).first()
                if step:
                    step.is_done = not step.is_done
                    session.commit()
                    print("🔁 Статус змінено.")
                else:
                    print("❌ Крок не знайдено.")
            except ValueError:
                print("❌ Невірний ID.")
        elif choice == "3":
            try:
                sid = int(input("ID кроку: ").strip())
                step = session.query(TaskStep).filter_by(id=sid, task_id=task.id).first()
                if step:
                    newtxt = input(f"Новий текст (Enter - залишити '{step.title}'): ").strip()
                    if newtxt:
                        step.title = newtxt
                        session.commit()
                        print("✅ Текст оновлено.")
                else:
                    print("❌ Крок не знайдено.")
            except ValueError:
                print("❌ Невірний ID.")
        elif choice == "4":
            try:
                sid = int(input("ID кроку для видалення: ").strip())
                step = session.query(TaskStep).filter_by(id=sid, task_id=task.id).first()
                if step:
                    confirm = input(f"Видалити крок '{step.title}'? (так/ні): ").strip().lower()
                    if confirm in ("так", "y", "yes"):
                        session.delete(step)
                        session.commit()
                        print("🗑️ Крок видалено.")
                else:
                    print("❌ Крок не знайдено.")
            except ValueError:
                print("❌ Невірний ID.")
        elif choice == "5":
            break
        else:
            print("❌ Невірний вибір.")


def delete_task(user: User):
    tasks = session.query(Task).filter_by(user_id=user.id).order_by(Task.id).all()
    if not tasks:
        print("📭 Немає завдань для видалення.")
        return
    print("\n=== Видалення завдання ===")
    for i, t in enumerate(tasks, 1):
        dl = format_deadline(t.deadline)
        print(f"{i}. [{t.id}] {t.title} — Дедлайн: {dl}")
    try:
        choice = int(input("\nВведіть номер завдання для видалення: ").strip())
    except ValueError:
        print("❌ Потрібно число.")
        return
    if not (1 <= choice <= len(tasks)):
        print("❌ Невірний номер.")
        return
    task = tasks[choice - 1]
    confirm = input(f"Ви точно хочете видалити '{task.title}'? (так/ні): ").strip().lower()
    if confirm not in ("так", "y", "yes"):
        print("❎ Видалення скасовано.")
        return
    session.delete(task)
    session.commit()
    print("✅ Завдання видалено.")


# ---- Меню ----
def task_menu(user: User):
    while True:
        print(f"\n=== Меню ({user.username}) ===")
        print("1) Переглянути завдання")
        print("2) Додати завдання")
        print("3) Редагувати завдання")
        print("4) Видалити завдання")
        print("5) Вийти")
        choice = input("Оберіть: ").strip()
        if choice == "1":
            view_tasks(user)
        elif choice == "2":
            add_task(user)
        elif choice == "3":
            edit_task(user)
        elif choice == "4":
            delete_task(user)
        elif choice == "5":
            break
        else:
            print("❌ Невірний вибір.")

def main_menu():
    while True:
        print("\n=== Головне меню ===")
        print("1) Увійти")
        print("2) Зареєструватися")
        print("3) Вийти")
        choice = input("Оберіть: ").strip()
        if choice == "1":
            user = login_user()
            if user:
                task_menu(user)
        elif choice == "2":
            u = register_user()
            if u:
                task_menu(u)
        elif choice == "3":
            print("👋 До побачення!")
            break
        else:
            print("❌ Невірний вибір.")

if __name__ == "__main__":
    main_menu()