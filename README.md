# JudaicaLink Labs

The JudaicaLink Portal for experimental access to our data.

Make sure [Python 3.8](https://www.python.org/downloads/release/python-382/) is installed!  
If you're running Windows you need to install [Visual Studio Build Tools](https://download.visualstudio.microsoft.com/download/pr/ac28b571-7709-4635-83d0-6277d6102ecb/ae0caec52ee10d6efc9b855bec5b934cf8054a638e08372e0de4f6351a25ea5d/vs_BuildTools.exe) with the C++ package.  



Clone the project ``` git clone https://github.com/wisslab/judaicalink-labs.git```  
In folder *labs* run ``` pip install -r requirements.txt --user```  
In *labs/labs* copy *settings_dev.py* in the same directory and name it *settings.py*  
In *labs* run ```python manage.py migrate``` command.

Download [Elasticsearch](https://www.elastic.co/de/downloads/elasticsearch) and unzip the downloaded file.  
Run elasticsearch:   
For Windows run the file in the unzipped folder *elasticsearch-x-x-x/bin/elasticsearch.bat*.


Create a super user for loading data:  
Navigate to JudaicaLink Labs Project in folder *labs* and run ```python manage.py createsuperuser```  
Now enter an username and a password. You can skip the email part.  

The server can now be started with ```python manage.py runserver```  and is accessible at [localhost:8000](http://localhost:8000).

To load the data go to [localhost:8000/admin](http://localhost:8000/admin) and login with your created super user.
- Select Datasets
- Click import from GitHub
- Select all datasets
- Select *action* "Index selected datasets and files"
- Click *Go*  

After completion click on "Load in Elasticsearch".

Now visit [localhost:8000/search](http://localhost:8000/search). You should now be able to search for data.  
___
If you encouter an ImplementationNotFoundError while starting the application with ```python manage.py runserver```  

>File "c:\users\user\appdata\local\programs\python\python38\lib\site-packages\tornado\platform\asyncio.py", line 99, in add_handler self.asyncio_loop.add_reader(fd, self._handle_events, fd, IOLoop.READ) File "c:\users\user\appdata\local\programs\python\python38\lib\asyncio\events.py", line 501, in add_reader raise NotImplementedError NotImplementedError

You can fix this error by changing some lines of code in Python38.  
Navigate to:  
*C:\Users{USER-NAME}\AppData\Local\Programs\Python\Python38\Lib\asyncio_init_.py*

and change it from:

```
if sys.platform == 'win32':  # pragma: no cover
    from .windows_events import *
    __all__ += windows_events.__all__
else:
    from .unix_events import *  # pragma: no cover
    __all__ += unix_events.__all__
```
to:  
```
import asyncio

if sys.platform == 'win32':
    from .windows_events import *
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    __all__ += windows_events.__all__
else:
    from .unix_events import *  # pragma:
```
Source: [Stackoverflow](https://stackoverflow.com/questions/58422817/jupyter-notebook-with-python-3-8-notimplementederror/58430041#58430041)
