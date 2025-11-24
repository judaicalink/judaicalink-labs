# Installation

## Installation under windows
To install the JudaicaLink website under windows, you have to perform the following steps

1.  Clone github repository.
* To run the JudaicaLink website on your local system clone the github repository.
* Make sure git is installed on your system:\
  Terminal: git --version
  * if not
    * Linux:   sudo apt install git-all (Debian) or sudo dnf install git-all (Fedora)
    * Windows:        Git for Windows installer
    * MacOS:          macOS Git Installer 
* Navigate to your target folder in your Terminal.
* Go to https://github.com/judaicalink/judaicalink-labs 
(for judaicalink-labs,to https://github.com/judaicalink/judaicalink-site for
judaicalink-site, to https://github.com/judaicalink/judaicalink-pubby for
judaicalink-pubby).
* Find the green "<>Code"-button and press.
* Copy the now showing HTTPS-code.
* Type: "git clone " and paste the copied HTTPS-code (press enter).
2.  Virtual environment (venv)
* To make sure all your requirements run under the right conditions create a virtual environment
* PyCharm brings this as an on-board function:
* To create a new virtual environment (venv) in PyCharm (on Windows), follow these steps:
    1. Open your PyCharm project.
    2. Click on "File" from the top menu bar, then "Settings".
    3. In the Settings window, click on "Project: <your project name>" in the left-hand sidebar, and then click on "Python Interpreter".
    4. Click „Add Interpreter“ in the top right corner, then „Add Local Interpreter“
       Now you should find the path to your project directory + „\venv“ in the appearing form.
    5. Press OK
    6. If you (re)open your terminal in pycharm your code line should start with „(venv) PS C:\Users\...“
3.  pip install requirements
* Navigate to the folder where you find the file "requirements.txt", in your terminal
* run the command "pip install -r requirements.txt --upgrade"
4. Rename the .sample folder (located in the labs folder) to ".env" and if necessary modify data.cd
5. Make sure django is installed on your system\
   Terminal: "py -m django --version" (Windows), "python -m django --version" (Linux, MacOS)
* You can install django on Windows by running "py -m pip install Django" and on Linux/MacOS by running "python -m pip install Django"
* for further help you find the django documentation under: https://docs.djangoproject.com/en/4.2/
6. Migrate
* If django is installed on your system (in your virtual environment), navigate to the folder where you find the file manage.py and run the command "py manage.py migrate"(Windows) or "python manage.py migrate" (Linux/MacOS)
7.  Collectstatic
* Run "py manage.py collectstatic"/"python manage.py collectstatic"
9. Start JudaicaLink
* Run "py manage.py runserver"/"python manage.py runserver"
* Open JudaicaLink in your Browser at: http://127.0.0.1:8000/

