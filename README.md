# pdf_processor
Processes the pdf and move forward to other site

# set up 
- `python3 -m venv env`
- `pip install -r requirements.txt`
- `cd document_processor`
- `python manage.py makemigrations`
- `python manage.py migrate`
- `python manage.py createsuperuser` (for the admin set up) 
- `python manage.py runserver`
- 

# Ensure the ODBC driver is installed
``` bash
macOS:
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
ACCEPT_EULA=Y brew install msodbcsql18
```
``` bash
Ubuntu/Debian:
sudo su
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
exit
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install msodbcsql18
```


How to Install sqlcmd
🧠 On macOS (you’re using macOS from your traceback)
``` bash
Run:

brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
ACCEPT_EULA=Y brew install mssql-tools18


Then add it to your PATH:

echo 'export PATH="/opt/homebrew/opt/mssql-tools18/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc


Now test it:

sqlcmd -?
```

If you see version info → installed ✅
``` bash
🧩 On Ubuntu / Debian
sudo su
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
exit
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install mssql-tools18 unixodbc-dev
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
source ~/.bashrc
```

Test the connection again
``` bash
python manage.py dbshell
```