echo "[i] finding python3 executable file..."

if test -x /usr/bin/python3 ; then 
    echo "[i] find /usr/bin/python3"
    echo "[i] getting root permission and setup..."
    sudo /usr/bin/python3 setup.py install
else
    echo "[E] cannot find python3 executable file"
fi
