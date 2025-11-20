import threading
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core import management
import io
from django.db import close_old_connections

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


def _command_target_wrapper(task_id, name, args, options):
    """
    Wrapper function that is executed in a parallel thread.
    All output is redirected to the task's log.
    """
    # für Thread: alte DB-Connections schließen
    close_old_connections()

    try:
        task = models.ThreadTask.objects.get(pk=task_id)
    except models.ThreadTask.DoesNotExist:
        # Falls versehentlich eine falsche ID übergeben wurde,
        # nicht mit Traceback sterben, sondern nur loggen.
        print(f"[ThreadTask] Task with id={task_id} does not exist.")
        return

    consumers.send_message(f'task{task_id}', 'info', task.name + ':', '')
    task.log("Task started.")
    try:
        taskStream = TaskStream(task)  # Helper class to capture all output of the command
        management.call_command(name, *args, **options, stdout=taskStream, stderr=taskStream)
        task.log("Task finished")
        task.done()
    except Exception as e:
        task.log("Task error: " + str(e))
        task.status_ok = False
        task.done()
        raise e

# labs/backend/tasks.py

def run_management_command(task_name, command, args=None, options=None):
    """
    Startet einen Management-Command asynchron als ThreadTask.

    task_name  = Anzeigename des Tasks (z.B. "generate_dataset:sosy")
    command    = Name des Django-Management-Commands (z.B. "generate_and_load_dataset")
    args       = Positionsargumente für den Command
    options    = Keyword-Argumente für den Command
    """
    if args is None:
        args = []
    if options is None:
        options = {}

    # ThreadTask mit sprechendem Namen anlegen
    task = models.ThreadTask()
    task.name = task_name
    task.save()
    task.refresh_from_db()

    # 'command' ist der wirkliche Django-Command, der ausgeführt werden soll
    t = threading.Thread(
        target=_command_target_wrapper,
        args=[task.id, command, args, options],
    )
    t.setDaemon(True)
    t.start()
    return task.id
