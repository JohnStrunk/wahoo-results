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
    pyinstaller --distpath=. --workpath=build wahoo-results.spec

::: After building the exe, put the original version file back
move /y version.py.save version.py
