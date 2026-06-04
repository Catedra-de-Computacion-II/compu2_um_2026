import os
import sys


print(f"PID padre {os.getpid()}")
pid = os.fork()

if pid == 0:
    print(f"PID hijo {os.getpid()}")
    # Hijo: ejecutar el comando
    os.execl("/bin/ls", "ls", "-l", "/home")

else:
    # Padre: esperar al hijo
    _, status = os.waitpid(pid, 0)

print(f"Terminó el código {os.getpid()}")
