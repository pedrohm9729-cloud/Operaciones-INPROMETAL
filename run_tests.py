import subprocess
import time
import sys
import os

def main():
    print("Iniciando run_tests.py...")
    my_pid = os.getpid()
    print(f"Mi PID es: {my_pid}")
    
    # Iniciar server.py en un subproceso
    print("Iniciando server.py...")
    server_process = subprocess.Popen(
        [sys.executable, 'server.py'],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    # Esperar a que el servidor se levante
    print("Esperando 3 segundos a que el servidor se inicie y vincule el puerto...")
    time.sleep(3)
    
    # Ejecutar test_security.py
    print("Ejecutando test_security.py...")
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    test_process = subprocess.Popen(
        [sys.executable, 'test_security.py'],
        env=env,
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    test_process.wait()
    exit_code = test_process.returncode
    
    # Terminar el servidor
    print("Terminando server.py...")
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_process.kill()
        
    print(f"Test suite finalizado con código de salida: {exit_code}")
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
