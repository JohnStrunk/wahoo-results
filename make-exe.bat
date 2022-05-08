@echo off

setlocal EnableDelayedExpansion

del wahoo-results.exe

::: Get the most recent git version tag
for /F "tokens=* usebackq" %%i IN (`git describe --tags --match "v*"` ) do (
    set version=%%i
)

::: Replace 'unreleased' with the version tag
move /y version.py version.py.save
for /F "tokens=* usebackq" %%i IN (version.py.save) do (
    set z=%%i
    echo !z:unreleased=%version%! >> version.py
)

pipenv run ^
pyinstaller --onefile ^
    --noconsole ^
    --distpath=. ^
    --workpath=build ^
    --add-data wahoo-results.ico;. ^
    --icon wahoo-results.ico ^
    --name wahoo-results ^
    wahoo_results.py

::: After building the exe, put the original version file back
move /y version.py.save version.py

::: Clean up build artifacts
del wahoo-results.spec
rmdir /q/s build

@REM ::: Create zip file
@REM :WaitUntilAccessible
@REM type wahoo-results.exe >NUL || goto :WaitUntilAccessible
@REM del wahoo-results.zip
@REM powershell Compress-Archive wahoo-results.exe wahoo-results.zip

@REM ::: Sign release artifact
@REM del wahoo-results.zip.asc
@REM gpg --detach-sign --armor --local-user BD1FF508 wahoo-results.zip
