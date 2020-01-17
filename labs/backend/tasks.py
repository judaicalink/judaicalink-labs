import threading
from . import models
'''
Task handling is based on:
https://github.com/nbwoodward/django-async-threading
'''
def start_task(target):
    '''
    Adapted from here:
    https://github.com/nbwoodward/django-async-threading/blob/master/thread/views.py
    '''
    task = models.ThreadTask()
    task.save()
    task.refresh_from_db()
    t = threading.Thread(target = _target_wrapper, args=[task.id, target])
    t.setDaemon(True)
    t.start()
    return task.id


def _target_wrapper(id, target):
    task = models.ThreadTask.objects.get(pk=id)
    task.log("Task started.")
    task.save()
    target(task)
    task.is_done = True
    task.log("Task finished")
    task.save()


