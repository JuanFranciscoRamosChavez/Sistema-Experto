from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
import string
from datetime import datetime
import hashlib

BASE_URL = "https://www.mayoclinic.org"
DISEASES_URL = f"{BASE_URL}/es/diseases-conditions"

def crear_hash_id(texto):
    """
    Crea un ID corto y único usando un hash SHA-1 a partir de un texto.
    """
    h = hashlib.sha1(texto.encode('utf-8'))
    return h.hexdigest()[:10]

def scrape_disease_list():
    """
    Configura Selenium y extrae el id, nombre y URL de todas las enfermedades.
    """
    service = Service()
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 10)
    print("Navegador Chrome iniciado por Selenium.")
    
    lista_unica_enfermedades = []

    try:
        letras = string.ascii_uppercase
        for letra in letras:
            print(f"\n--- Procesando letra: {letra} ---")
            
            url_letra = f"{DISEASES_URL}/index?letter={letra}"
            driver.get(url_letra)
            
            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cmp-result-name__link")))
                enlaces_elementos = driver.find_elements(By.CLASS_NAME, "cmp-result-name__link")
                
                if not enlaces_elementos:
                    print(f"No se encontraron enfermedades para la letra '{letra}'.")
                    continue

                print(f"Se encontraron {len(enlaces_elementos)} enfermedades para la letra '{letra}'.")

                for enlace in enlaces_elementos:
                    nombre = enlace.text
                    url = enlace.get_attribute('href')
                    
                    if nombre and url:
                        id_enfermedad = crear_hash_id(url)
                        lista_unica_enfermedades.append({
                            "id": id_enfermedad,
                            "nombre": nombre,
                            "url": url
                        })
            
            except TimeoutException:
                print(f"No se encontraron resultados para la letra '{letra}' o la página no cargó a tiempo.")

    except Exception as e:
        print(f"\nOcurrió un error general en el proceso: {e}")
    finally:
        print("\nScraping finalizado. Cerrando el navegador.")
        driver.quit()
        
    return lista_unica_enfermedades

def verificar_duplicados(lista_enfermedades):
    """
    Revisa la lista de enfermedades para encontrar IDs duplicados.
    """
    print("\n--- Verificando la integridad de los IDs ---")
    ids_vistos = set()
    duplicados = []
    for enfermedad in lista_enfermedades:
        id_actual = enfermedad["id"]
        if id_actual in ids_vistos:
            duplicados.append(id_actual)
        else:
            ids_vistos.add(id_actual)
    
    if not duplicados:
        print(" ¡Excelente! No se encontraron IDs duplicados.")
    else:
        print(f" ¡Atención! Se encontraron {len(duplicados)} IDs duplicados:")
        # Imprime solo los duplicados únicos para no saturar la consola
        for id_duplicado in set(duplicados):
            print(f"  - ID: {id_duplicado}")
    print("="*60)

if __name__ == "__main__":
    enfermedades_extraidas = scrape_disease_list()
    
    if enfermedades_extraidas:
        # Primero, verifica si hay duplicados en los datos extraídos
        verificar_duplicados(enfermedades_extraidas)

        datos_finales = {
            "metadata": {
                "fuente": DISEASES_URL,
                "total_registros": len(enfermedades_extraidas)
            },
            "enfermedades": enfermedades_extraidas
        }

        try:
            with open('1_lista_enfermedades.json', 'w', encoding='utf-8') as f:
                json.dump(datos_finales, f, ensure_ascii=False, indent=4)
            print("¡Proceso completado con éxito!")
            print("Los datos se han guardado en '1_lista_enfermedades.json'")
            print("="*60)
        except IOError as e:
            print(f"Error al guardar el archivo JSON: {e}")
    else:
        print("\nNo se pudo extraer ninguna información. El proceso falló.")