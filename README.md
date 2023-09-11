# QOL-Updater
Small wizard to help advise and apply QOL patches for ElDewrito.


### Build:
'''
pyinstaller --noconfirm --onefile --windowed --add-data "C:\Users\{user}\AppData\Local\Programs\Python\Python311\Lib\site-packages\customtkinter;customtkinter/" --add-data "assets;assets/" updater.py
'''
