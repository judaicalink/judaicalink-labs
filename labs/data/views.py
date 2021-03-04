from django.shortcuts import render
from django.http import HttpResponse
from django.core import management

# Create your views here.

def index(request):
    all_cmds = management.get_commands()
    cmds = []
    for cmd, app in all_cmds.items():
        if app=='data':
            cmd_class = management.load_command_class("data", cmd)
            cmd_class.name = cmd
            cmds.append(cmd_class)

    return render(request, 'data/index.html', {"cmds": cmds})

