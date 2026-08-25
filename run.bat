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

echo [1/6] Lettura delle fonti TEI...
python tools\0_parse_tei.py
if errorlevel 1 (
    echo ERRORE in tools\0_parse_tei.py
    pause
    exit /b 1
)

echo.
echo [2/6] Verifica del testo italiano...
python tools\1_validate_translation.py
if errorlevel 1 (
    echo ERRORE: il testo italiano non e' completo o non e' valido.
    pause
    exit /b 1
)

echo.
echo [3/6] Generazione delle pagine del sito...
python tools\2_generate_site.py
if errorlevel 1 (
    echo ERRORE in tools\2_generate_site.py
    pause
    exit /b 1
)

echo.
echo [4/6] Generazione del sorgente del PDF italiano...
python tools\3_generate_pdf_book.py
if errorlevel 1 (
    echo ERRORE in tools\3_generate_pdf_book.py
    pause
    exit /b 1
)

echo.
echo [5/6] Render del sito...
"%QUARTO%" render
if errorlevel 1 (
    echo ERRORE durante quarto render
    pause
    exit /b 1
)

echo.
echo [6/6] Render del PDF italiano...
"%QUARTO%" render pdf_book_it.qmd --to pdf
if errorlevel 1 (
    echo ERRORE durante il render del PDF.
    echo.
    echo Se e' la prima volta che si genera un PDF con Quarto, eseguire:
    echo quarto install tinytex
    echo.
    pause
    exit /b 1
)

rem Quando si renderizza un singolo file non incluso nel progetto web, alcune
rem versioni di Quarto ignorano project.output-dir e scrivono accanto al QMD.
rem In quel caso spostiamo esplicitamente il PDF nella cartella pubblicata.
if exist epitteto-diatribe-it.pdf (
    move /Y epitteto-diatribe-it.pdf docs\epitteto-diatribe-it.pdf >nul
)

if not exist docs\epitteto-diatribe-it.pdf (
    echo ERRORE: il PDF non e' stato scritto in docs.
    pause
    exit /b 1
)

echo.
echo Fatto.
echo Sito: docs\
echo PDF:  docs\epitteto-diatribe-it.pdf
echo.
pause
