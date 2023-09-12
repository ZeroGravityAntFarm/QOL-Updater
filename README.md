# QOL-Updater
Small wizard to help advise and apply QOL patches for ElDewrito.

![dewupdater](/assets/updater.PNG)

### Build:

Requirements: \
python 3.11.5 \
pyinstaller 5.13.2 \
customtkinter 5.2.0 \
PIL 10.0.0 \
gputil 1.4.0

```
pyinstaller --noconfirm --onefile --windowed --add-data "C:\Users\{user}\AppData\Local\Programs\Python\Python311\Lib\site-packages\customtkinter;customtkinter/" --add-data "assets;assets/" --splash "assets\slayer.png" --icon=assets\favicon.ico updater.py
```
