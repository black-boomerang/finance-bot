# Класс scheduler'а для вызова функции в запланированное время.
# Работает в отдельном потоке

from threading import Thread

from apscheduler.schedulers.blocking import BlockingScheduler


class ScheduleThread(Thread):
    def __init__(self):
        super().__init__()
        self.scheduler = BlockingScheduler()

    def add_job(self, function_to_run, *args, **kwargs):
        self.scheduler.add_job(function_to_run, *args, **kwargs)

    def run(self):
        self.scheduler.start()
