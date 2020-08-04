import threading
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core import management
import io
from . import models
from . import consumers
'''
Task handling is based on:
https://github.com/nbwoodward/django-async-threading
'''


class TaskStream(io.TextIOBase):
    '''
    TaskStream is used as a redirect for the stdout and 
    stderr streams, so that all output of commands is
    sent to the task log.
    '''
    def __init__(self, task):
        self.task = task

    def write(self, s):
        self.task.log(s)
        return len(s)




def call_command_as_task(name, *args, **options):
    '''
    Adapted from here:
    https://github.com/nbwoodward/django-async-threading/blob/master/thread/views.py

    Creates a new task for the given command name.
    '''
    task = models.ThreadTask()
    task.name = name
    task.save()
    task.refresh_from_db()
    t = threading.Thread(target = _command_target_wrapper, args=[task.id, name, args, options])
    t.setDaemon(True)
    t.start()
    return task.id


def _command_target_wrapper(id, name, args, options):
    '''
    Wrapper function that is executed in a parallel thread.
    All output is redirected to the task's log.
    '''
    task = models.ThreadTask.objects.get(pk=id) # as this is running in an own thread, we have to get the task from DB.
    consumers.send_message('task{}'.format(id), 'info', task.name + ':', '') 
    task.log("Task started.")
    try:
        taskStream = TaskStream(task) # Helper class to capture all output of the command
        # Here, the actual command is called and stdout and stderr are redirected.
        management.call_command(name, *args, **options, stdout=taskStream, stderr=taskStream) 
        task.log("Task finished")
        task.done()
    except Exception as e:
        task.log("Task error: " + str(e))
        task.status_ok = False
        task.done()
        raise e


