::: Create & activate virtual environment
python -m venv venv
call venv\Scripts\activate.bat

::: Upgrade pip to latest
python -m pip install --upgrade pip

::: Install dependencies
pip install --upgrade -r requirements.txt