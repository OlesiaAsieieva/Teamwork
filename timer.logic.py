import threading
import time

class Timer:
    def __init__(self, minutes=0, seconds=0, on_tick=None, on_finish=None, on_stop=None):
        """
        minutes, seconds - початковий час
        on_tick - функція викликається кожну секунду (оновлення відліку)
        on_finish - функція викликається коли таймер завершився
        on_stop - функція викликається коли користувач зупинив таймер
        """
        self.total_seconds = minutes * 60 + seconds
        self.remaining_seconds = self.total_seconds
        self.on_tick = on_tick
        self.on_finish = on_finish
        self.on_stop = on_stop
        self.running = False
        self._thread = None

    def start(self):
        """Запуск таймера"""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
    def _run(self):
        while self.remaining_seconds > 0 and self.running:
            mins, secs = divmod(self.remaining_seconds, 60)
            if self.on_tick:
                self.on_tick(mins, secs)
            time.sleep(1)
            self.remaining_seconds -= 1

        if self.remaining_seconds == 0 and self.running:
            if self.on_finish:
                self.on_finish()
        self.running = False

    def stop(self, confirm_stop=True):
        if confirm_stop and self.on_stop:
            if not self.on_stop():  # якщо користувач не підтвердив, нічого не робимо
                return
        self.running = False
        self.remaining_seconds = self.total_seconds

    def reset(self, minutes=None, seconds=None):
        """Скидання таймера на початковий або новий час"""
        self.running = False
        if minutes is not None or seconds is not None:
            minutes = minutes or 0
            seconds = seconds or 0
            self.total_seconds = minutes * 60 + seconds
        self.remaining_seconds = self.total_seconds
        if self.on_tick:
            mins, secs = divmod(self.remaining_seconds, 60)
            self.on_tick(mins, secs)
