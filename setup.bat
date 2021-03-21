SET PyBin=C:\Windows\py.exe

if exist %PyBin% (
    C:\Windows\py.exe setup.py install
) else (
    echo [E] Cannot find python executable file: %PyBin%
    pause>nul
)