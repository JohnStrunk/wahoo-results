@echo off

uv export --locked --format requirements-txt > requirements.txt
uv tool run pip-audit -r requirements.txt --desc on --require-hashes --disable-pip
del requirements.txt
