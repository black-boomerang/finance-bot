# Класс scheduler'а для вызова функции в запланированное время. Работает в отдельном потоке

from threading import Thread

from apscheduler.schedulers.blocking import BlockingScheduler


class ScheduleThread(Thread):
    def __init__(self, function_to_run, *args, **kwargs):
        super().__init__()
        self.scheduler = BlockingScheduler()

        @self.scheduler.scheduled_job(*args, **kwargs)
        def timed_job():
            function_to_run()

    def run(self):
        self.scheduler.start()
