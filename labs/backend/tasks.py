import threading
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from . import models
'''
Task handling is based on:
https://github.com/nbwoodward/django-async-threading
'''
def start_task(name, target):
    '''
    Adapted from here:
    https://github.com/nbwoodward/django-async-threading/blob/master/thread/views.py
    '''
    task = models.ThreadTask()
    task.name = name
    task.save()
    task.refresh_from_db()
    t = threading.Thread(target = _target_wrapper, args=[task.id, target])
    t.setDaemon(True)
    t.start()
    return task.id


def _target_wrapper(id, target):
    task = models.ThreadTask.objects.get(pk=id)
    task.log("Task started.")
    target(task)
    task.log("Task finished")
    task.done()


