from django.shortcuts import render
from django.http import HttpResponse
from django.core import management
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.core.cache.backends.base import DEFAULT_TIMEOUT

# Create your views here.
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

@cache_page(CACHE_TTL)
def index(request):
    all_cmds = management.get_commands()
    cmds = []
    for cmd, app in all_cmds.items():
        if app=='data':
            cmd_class = management.load_command_class("data", cmd)
            cmd_class.name = cmd
            cmds.append(cmd_class)

    return render(request, 'data/index.html', {"cmds": cmds})

