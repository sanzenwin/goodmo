setlocal enabledelayedexpansion
@echo off

:argsLoop
if "%1"=="" (if "!args!" neq "" ( set args=!args:~1!) ) else ( set "args=!args! %1"&shift /1&goto :argsLoop)

cd ../..
set curpath=%cd%

cd ..
set KBE_ROOT=%cd%
set KBE_RES_PATH=%KBE_ROOT%/kbe/res/;%curpath%/;%curpath%/res/;%curpath%/scripts/;%curpath%/scripts/res/
set KBE_BIN_PATH=%KBE_ROOT%/kbe/bin/server/

if defined uid (echo UID = %uid%) else (echo must set 'uid' environment variable && pause)


cd %curpath%
call "scripts/shell/kill_server"

echo KBE_ROOT = %KBE_ROOT%
echo KBE_RES_PATH = %KBE_RES_PATH%
echo KBE_BIN_PATH = %KBE_BIN_PATH%

set KBE_PLUGINS__AUTO_GENERATE=1
set KBE_PLUGINS__ARGS=%args%
start %KBE_BIN_PATH%/baseapp.exe --cid=10001 --gus=1
