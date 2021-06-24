
[Install python](https://www.python.org/ftp/python/3.9.5/python-3.9.5-amd64.exe)
[Install tesseract](https://github.com/UB-Mannheim/tesseract/wiki)

 may need to logout/reboot to get python in path
```
pip install -r requirements.txt
pyinstaller -w  dcs_wp_editor.py 
```
ensure map.bin and arrow.bin are in root dir for install


pyinstaller -w -F dcs_wp_editor.py 