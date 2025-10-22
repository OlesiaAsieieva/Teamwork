from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, UTC

Base = declarative_base()

# --- Користувач ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), unique=True)
    password_hash = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    tasks = relationship("Task", back_populates="user")

# --- Завдання ---
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="active")
    deadline = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    user = relationship("User", back_populates="tasks")
    steps = relationship("TaskStep", back_populates="task", cascade="all, delete-orphan")

# --- Кроки завдання ---
class TaskStep(Base):
    __tablename__ = "task_steps"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    title = Column(String(100), nullable=False)
    is_done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    task = relationship("Task", back_populates="steps")

# --- Підключення до бази ---
engine = create_engine("sqlite:///learning_app.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# --- Основне меню ---
def main_menu():
    while True:
        print("\n--- 📘 СИСТЕМА КЕРУВАННЯ ЗАВДАННЯМИ ---")
        print("1. Додати користувача")
        print("2. Створити завдання")
        print("3. Додати крок до завдання")
        print("4. Позначити крок як виконаний")
        print("5. Переглянути всі завдання")
        print("6. Вийти")

        choice = input("Ваш вибір: ")

        if choice == "1":
            add_user()
        elif choice == "2":
            add_task()
        elif choice == "3":
            add_step()
        elif choice == "4":
            mark_step_done()
        elif choice == "5":
            show_all()
        elif choice == "6":
            print("👋 Вихід із програми.")
            break
        else:
            print("❌ Невірний вибір!")

# --- Додавання користувача ---
def add_user():
    username = input("Введіть ім'я користувача: ")
    email = input("Введіть email: ")
    password = input("Введіть пароль: ")

    user = User(username=username, email=email, password_hash=password)
    session.add(user)
    session.commit()
    print(f"✅ Користувача '{username}' додано!")

# --- Додавання завдання ---
def add_task():
    username = input("Для якого користувача створити завдання? (ім'я): ")
    user = session.query(User).filter_by(username=username).first()
    if not user:
        print("❌ Користувача не знайдено!")
        return

    title = input("Назва завдання: ")
    desc = input("Опис: ")
    deadline_input = input("Дедлайн (РРРР-ММ-ДД): ")
    deadline = datetime.strptime(deadline_input, "%Y-%m-%d")

    task = Task(title=title, description=desc, deadline=deadline, user=user)
    session.add(task)
    session.commit()
    print(f"✅ Завдання '{title}' створено для користувача {username}!")

# --- Додавання кроку ---
def add_step():
    task_title = input("Для якого завдання додати крок? (назва): ")
    task = session.query(Task).filter_by(title=task_title).first()
    if not task:
        print("❌ Завдання не знайдено!")
        return

    title = input("Назва кроку: ")
    step = TaskStep(title=title, task=task)
    session.add(step)
    session.commit()
    print(f"✅ Крок '{title}' додано до завдання '{task_title}'!")

# --- Позначення кроку як виконаного ---
def mark_step_done():
    step_title = input("Введіть назву кроку, який виконано: ")
    step = session.query(TaskStep).filter_by(title=step_title).first()
    if not step:
        print("❌ Крок не знайдено!")
        return

    step.is_done = True
    session.commit()
    print(f"✅ Крок '{step_title}' позначено як виконаний!")

# --- Перегляд усіх даних ---
def show_all():
    users = session.query(User).all()
    if not users:
        print("📭 Немає користувачів або завдань.")
        return

    for user in users:
        print(f"\n👤 {user.username} ({user.email})")
        for task in user.tasks:
            print(f"  📋 {task.title} — {task.status} (до {task.deadline.date()})")
            for step in task.steps:
                icon = "✅" if step.is_done else "🔸"
                print(f"     {icon} {step.title}")

# --- Запуск ---
if __name__ == "__main__":
    main_menu()
