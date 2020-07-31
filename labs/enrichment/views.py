from django.shortcuts import render
from django.http import HttpResponse
from django.core import management

# Create your views here.

def index(request):
    all_cmds = management.get_commands()
    cmds = []
    for cmd, app in all_cmds.items():
        if app=='enrichment':
            cmd_class = management.load_command_class("enrichment", cmd)
            cmd_class.name = cmd
            cmds.append(cmd_class)

    return render(request, 'enrichment/index.html', {"cmds": cmds})

