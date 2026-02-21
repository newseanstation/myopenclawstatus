@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

REM ==============================================================
REM run_all.bat
REM Purpose:
REM   1) Generate original-language subtitles (ZH SRT) with Whisper
REM   2) Translate speech to English subtitles (EN SRT) with Whisper
REM   3) Convert EN SRT -> ASS (optional but recommended)
REM   4) Burn ASS into video (hard subtitles)
REM
REM Usage:
REM   - Drag and drop your video onto this .bat, OR
REM   - Run: run_all.bat "G:\path\to\video.mp4"
REM
REM Notes:
REM   - Adjust PYTHON_EXE below to your actual python.exe path.
REM   - Requires ffmpeg available in PATH.
REM ==============================================================

REM --- CONFIG: set your Python executable path (portable python in your setup)
set "PYTHON_EXE=G:\SadTalker\python310\python.exe"

REM --- INPUT
if "%~1"=="" (
  echo.
  echo [ERROR] No input video specified.
  echo Drag^&drop a video onto this bat, or run:
  echo   %~nx0 "G:\soundscreen\SabbaShopGuide.mp4"
  echo.
  exit /b 2
)

set "IN_VIDEO=%~1"

REM --- Resolve working directory to the input video's folder
for %%F in ("%IN_VIDEO%") do (
  set "IN_DIR=%%~dpF"
  set "IN_NAME=%%~nF"
  set "IN_EXT=%%~xF"
)

pushd "%IN_DIR%" || (echo [ERROR] Cannot cd to input folder: "%IN_DIR%" & exit /b 3)

REM --- Basic checks
if not exist "%PYTHON_EXE%" (
  echo.
  echo [ERROR] Python not found at:
  echo   %PYTHON_EXE%
  echo Edit PYTHON_EXE at the top of this file.
  echo.
  popd
  exit /b 4
)

where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo.
  echo [ERROR] ffmpeg not found in PATH.
  echo Install ffmpeg (e.g. winget install Gyan.FFmpeg) and reopen CMD.
  echo.
  popd
  exit /b 5
)

REM --- Output folders
set "OUT_ZH=%IN_DIR%out_zh"
set "OUT_EN=%IN_DIR%out_en"
if not exist "%OUT_ZH%" mkdir "%OUT_ZH%" >nul 2>nul
if not exist "%OUT_EN%" mkdir "%OUT_EN%" >nul 2>nul

echo.
echo ==============================================================
echo Input video : "%IN_VIDEO%"
echo Output (ZH) : "%OUT_ZH%\%IN_NAME%.srt"
echo Output (EN) : "%OUT_EN%\%IN_NAME%.srt"
echo ==============================================================
echo.

REM --- 1) Original-language subtitles (ZH)
echo [1/4] Generating original-language subtitles (transcribe)...
"%PYTHON_EXE%" -m whisper "%IN_VIDEO%" --task transcribe --output_format srt --output_dir "%OUT_ZH%" --verbose False
if errorlevel 1 (
  echo.
  echo [ERROR] Whisper transcribe failed.
  popd
  exit /b 10
)

REM --- 2) English subtitles (translate)
echo.
echo [2/4] Translating speech to English subtitles (translate)...
"%PYTHON_EXE%" -m whisper "%IN_VIDEO%" --task translate --model medium --output_format srt --output_dir "%OUT_EN%" --initial_prompt "Translate all speech to English. Output English only." --verbose False
if errorlevel 1 (
  echo.
  echo [ERROR] Whisper translate failed.
  popd
  exit /b 11
)

REM --- 3) Convert EN SRT -> ASS (recommended for burning)
set "EN_SRT=%OUT_EN%\%IN_NAME%.srt"
set "EN_ASS=%OUT_EN%\%IN_NAME%.ass"
echo.
echo [3/4] Converting EN SRT to ASS...
ffmpeg -y -i "%EN_SRT%" "%EN_ASS%" >nul
if errorlevel 1 (
  echo.
  echo [WARN] SRT->ASS conversion failed. Will attempt to burn SRT directly.
)

REM --- 4) Burn subtitles into video
REM IMPORTANT: Avoid drive-letter parsing issues inside ffmpeg filters by copying subtitle to current dir
echo.
echo [4/4] Burning subtitles into video...
set "OUT_VIDEO=%IN_DIR%%IN_NAME%_en_subbed%IN_EXT%"

if exist "%EN_ASS%" (
  copy /y "%EN_ASS%" "%IN_DIR%sub.ass" >nul
  ffmpeg -y -i "%IN_VIDEO%" -vf "ass=sub.ass" -c:a copy "%OUT_VIDEO%"
) else (
  copy /y "%EN_SRT%" "%IN_DIR%sub.srt" >nul
  ffmpeg -y -i "%IN_VIDEO%" -vf "subtitles=sub.srt" -c:a copy "%OUT_VIDEO%"
)

if errorlevel 1 (
  echo.
  echo [ERROR] Burning subtitles failed.
  echo Tip: Ensure the video and sub.ass/sub.srt are in the same folder.
  popd
  exit /b 12
)

REM --- Done
echo.
echo [OK] Done.
echo ZH SRT : "%OUT_ZH%\%IN_NAME%.srt"
echo EN SRT : "%OUT_EN%\%IN_NAME%.srt"
echo Output : "%OUT_VIDEO%"
echo.

popd
endlocal
exit /b 0
