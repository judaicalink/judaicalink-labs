import threading
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from . import models
from . import consumers
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
    consumers.send_message('task{}'.format(id), 'info', task.name + ':', '') 
    task.log("Task started.")
    try:
        target(task)
        task.log("Task finished")
        task.done()
    except Exception as e:
        task.log("Task error: " + str(e))
        task.status_ok = False
        task.done()
        raise e


