::: Create & activate virtual environment
python -m venv venv || goto :error
call venv\Scripts\activate.bat || goto :error

::: Upgrade pip to latest
python -m pip install --upgrade pip wheel || goto :error

::: Install dependencies
pip install --upgrade -r requirements.txt || goto :error


goto :EOF
:error
echo Failed with error: #%errorlevel%
exit /b %errorlevel%