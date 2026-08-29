@echo off
title Miyoo Mini Plus ^& OnionOS Studio / Simulator
cd /d "%~dp0"
python run.py
if errorlevel 1 (
    echo.
    echo An error occurred while running the simulator.
    pause
)
