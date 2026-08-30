@echo off
setlocal

echo.
echo === Epitteto, Diatribe: costruzione del sito e del PDF ===
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo ERRORE: python non trovato nel PATH.
    pause
    exit /b 1
)

for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)"') do set "QUARTO_PYTHON=%%P"

set "QUARTO=quarto"
where quarto >nul 2>nul
if errorlevel 1 (
    if exist "%LOCALAPPDATA%\Programs\Quarto\bin\quarto.exe" (
        set "QUARTO=%LOCALAPPDATA%\Programs\Quarto\bin\quarto.exe"
    ) else (
        echo ERRORE: quarto non trovato nel PATH ne' nell'installazione locale.
        pause
        exit /b 1
    )
)

echo [1/5] Lettura delle fonti TEI...
python tools\0_parse_tei.py
if errorlevel 1 (
    echo ERRORE in tools\0_parse_tei.py
    pause
    exit /b 1
)

echo.
echo [2/5] Verifica del testo italiano...
python tools\1_validate_translation.py
if errorlevel 1 (
    echo ERRORE: il testo italiano non e' completo o non e' valido.
    pause
    exit /b 1
)

echo.
echo [3/5] Generazione delle pagine del sito...
python tools\2_generate_site.py
if errorlevel 1 (
    echo ERRORE in tools\2_generate_site.py
    pause
    exit /b 1
)

echo.
echo [4/5] Generazione del sorgente del PDF italiano...
python tools\3_generate_pdf_book.py
if errorlevel 1 (
    echo ERRORE in tools\3_generate_pdf_book.py
    pause
    exit /b 1
)

echo.
echo [5/5] Render incrementale del sito e del PDF...
rem Renderizza solo le pagine toccate da un cambiamento. "run.bat --full" forza
rem il render completo; cancellare .render-cache.json ha lo stesso effetto.
set "QUARTO_BIN=%QUARTO%"
python tools\5_render.py %*
if errorlevel 1 (
    echo ERRORE durante il render.
    echo.
    echo Se e' la prima volta che si genera un PDF con Quarto, eseguire:
    echo quarto install tinytex
    echo.
    pause
    exit /b 1
)

echo.
echo Fatto.
echo Sito: docs\
echo PDF:  docs\epitteto-diatribe-it.pdf
echo.
pause
