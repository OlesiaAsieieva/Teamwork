import threading
import time
import json
from datetime import datetime

class Timer:
    def __init__(self, minutes=0, seconds=0, on_tick=None, on_finish=None, stats_file="stats.json"):
        self.total_seconds = minutes * 60 + seconds
        self.remaining_seconds = self.total_seconds
        self.on_tick = on_tick
        self.on_finish = on_finish
        self.running = False
        self._thread = None
        self.start_time = None
        self.elapsed_seconds = 0
        self.stats_file = stats_file

    def start(self):
        if self.running:
            return
        self.running = True
        self.start_time = time.time()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while self.remaining_seconds > 0 and self.running:
            mins, secs = divmod(self.remaining_seconds, 60)
            if self.on_tick:
                self.on_tick(mins, secs)
            time.sleep(1)
            self.remaining_seconds -= 1
            self.elapsed_seconds = self.total_seconds - self.remaining_seconds

        if self.remaining_seconds == 0 and self.running:
            if self.on_finish:
                self.on_finish()
            self._save_stats()
        self.running = False

    def stop(self):
        if self.running:
            self.running = False
            self.elapsed_seconds = self.total_seconds - self.remaining_seconds
            self._save_stats()

    def reset(self, minutes=None, seconds=None):
        self.running = False
        if minutes is not None or seconds is not None:
            minutes = minutes or 0
            seconds = seconds or 0
            self.total_seconds = minutes * 60 + seconds
        self.remaining_seconds = self.total_seconds
        self.elapsed_seconds = 0
        if self.on_tick:
            mins, secs = divmod(self.remaining_seconds, 60)
            self.on_tick(mins, secs)

    def _save_stats(self):
        """Зберігає тривалість сеансу у JSON"""
        data = []
        try:
            with open(self.stats_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        data.append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration_minutes": round(self.elapsed_seconds / 60, 2)
        })

        with open(self.stats_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
