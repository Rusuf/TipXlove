@echo off
REM Database migration helper script

if "%1"=="init" (
    python manage.py init-db
    goto :eof
)

if "%1"=="migrate" (
    if "%2"=="" (
        python manage.py migrate
    ) else (
        python manage.py migrate -m %2
    )
    goto :eof
)

if "%1"=="upgrade" (
    python manage.py upgrade
    goto :eof
)

if "%1"=="downgrade" (
    if "%2"=="" (
        echo Error: Please provide a revision to downgrade to
        goto :usage
    )
    python manage.py downgrade -r %2
    goto :eof
)

if "%1"=="admin" (
    python manage.py create-admin
    goto :eof
)

:usage
echo.
echo Database Management Script
echo -------------------------
echo Usage:
echo   db_migrate.bat init               - Initialize the database
echo   db_migrate.bat migrate [message]  - Create a new migration
echo   db_migrate.bat upgrade            - Upgrade database to latest version
echo   db_migrate.bat downgrade rev      - Downgrade database to revision
echo   db_migrate.bat admin              - Create an admin user
echo. 