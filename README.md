# JudaicaLink Labs

The JudaicaLink Portal for experimental access to our data.


JudaicaLink labs Seite starten:

1.) Django Framework installieren.
2.) wisslab/judaicalink-labs clonen (am besten in der Shell: git clone ...HTTP Link...)
3.) in Administrator Shell: judaicalink-labs\labs\pip install -r requirements.txt oder in der normalen Shell: judaicalink-labs\labs\pip install -r requirements.txt -- user 
4.) \labs\py manage.py runserver (Server starten)
5.) settings.py(lokal) immer mit der settings_dev.py aktualisieren, weil das nicht automatisch passiert, beim ersten mal settings_dev.py einfach kopieren und in settings.py umbenennen, sodass man am Ende settings.py und settings_dev.py hat.
6.) \labs\py manage.py migrate
7.) \labs\py manage.py runserver
8.) im Browser aufrufen: localhost:8000 FERTIG! :D


Elastic Search starten:

1.) Elastic Search installieren
2.) bat-Datei ausführen
3.) Admin shell: \labs\py manage.py createsuperuser (wichtig für backend)
4.) Username + Passwort merken (E-Mail kann man überspringen (leer lassen))
5.) \labs\py manage.py runserver (Server starten)
6.) localhost:8000/admin FERTIG! :D


Python 3.8 installieren, 64 bit Version: (evtl. muss man Microsoft Visual Studio auch installieren)

https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.6.2-windows-x86_64.zip
Bei Verwendung von Python 3.8 wird eventuell ein Fehler angezeigt.

  File "c:\users\user\appdata\local\programs\python\python38\lib\site-packages\tornado\platform\asyncio.py", line 99, in add_handler
    self.asyncio_loop.add_reader(fd, self._handle_events, fd, IOLoop.READ)
  File "c:\users\user\appdata\local\programs\python\python38\lib\asyncio\events.py", line 501, in add_reader
    raise NotImplementedError
NotImplementedError

Um diesen Fehler zu beheben muss unter 

C:\Users\{USER-NAME}\AppData\Local\Programs\Python\Python38\Lib\asyncio\__init__.py


von:
```
if sys.platform == 'win32':  # pragma: no cover
    from .windows_events import *
    __all__ += windows_events.__all__
else:
    from .unix_events import *  # pragma: no cover
    __all__ += unix_events.__all__
```
zu
```
import asyncio

if sys.platform == 'win32':
    from .windows_events import *
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    __all__ += windows_events.__all__
else:
    from .unix_events import *  # pragma:
```

Quelle: (14.04.2020)
https://stackoverflow.com/questions/58422817/jupyter-notebook-with-python-3-8-notimplementederror/58430041#58430041



