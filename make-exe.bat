del wahoo-results.exe

python -m venv venv
call venv\Scripts\activate.bat

python -m pip install --upgrade pip
pip install --upgrade -r requirements.txt

pyinstaller --onefile --noconsole --distpath=. --workpath=build --version-file=wahoo-results.version wahoo-results.py

del wahoo-results.spec
rmdir /q/s build