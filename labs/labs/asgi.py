"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os
import django
from channels.auth import AuthMiddlewareStack
from channels.routing import get_default_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "labs.settings")
django_asgi_app = get_asgi_application()

#django.setup()
#application = get_default_application()

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,

    # WebSocket chat handler
    #'websocket': AuthMiddlewareStack(
    #    URLRouter(
    #        )
    #),
                                                                                            })
