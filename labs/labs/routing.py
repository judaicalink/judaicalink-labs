from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import data.routing
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            data.routing.websocket_urlpatterns
        )
    ),
})
