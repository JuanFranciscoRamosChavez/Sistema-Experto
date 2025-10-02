from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import json
import time

"""
Script para extraer detalles completos de cada enfermedad del sitio web de Mayo Clinic en español.
Utiliza Selenium para manejar contenido dinámico y BeautifulSoup para parsear el HTML.
Navega por las pestañas de cada página de enfermedad para obtener información estructurada.
Guarda los datos en un archivo JSON.
"""


# --- CONFIGURACIÓN ---
SECCIONES_SINTOMAS_CAUSAS = [
    """
    Detalles de las secciones a extraer de la pestaña principal (Síntomas y causas).
    """
    "descripción general",
    "síntomas", 
    "causas",
    "factores de riesgo",
    "complicaciones",
    "prevención"
]

SECCIONES_DIAGNOSTICO_TRATAMIENTO = [
    """
    Detalles de las secciones a extraer de la pestaña (Diagnóstico y tratamiento
    """
    "diagnóstico",
    "tratamiento"
]

"""
Nombres de los archivos de entrada y salida.
"""

ARCHIVO_ENTRADA = '1_lista_enfermedades.json'
ARCHIVO_SALIDA = '2_enfermedades_detallado_crudo.json'

def hacer_clic_pestana(driver, nombre_pestana):
    """Hace clic en una pestaña específica del menú de navegación."""
    try:
        # Buscar el elemento del menú por el texto
        if "diagnóstico" in nombre_pestana.lower():
            selector = 'a[id*="diagnosis-treatment"], a[href*="diagnosis-treatment"]'
        elif "médicos" in nombre_pestana.lower():
            selector = 'a[id*="doctors-departments"], a[href*="doctors-departments"]'
        else:
            # Para síntomas y causas (página principal)
            return True
            
        elemento_menu = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        
        # Hacer clic en el elemento
        driver.execute_script("arguments[0].click();", elemento_menu)
        
        # Esperar a que la página cargue
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h2"))
        )
        
        print(f"      -> Clic en '{nombre_pestana}' exitoso")
        time.sleep(2)  # Espera adicional para asegurar la carga
        return True
        
    except TimeoutException:
        print(f"      -> No se encontró la pestaña '{nombre_pestana}'")
        return False
    except Exception as e:
        print(f"      -> ERROR al hacer clic en '{nombre_pestana}': {e}")
        return False

def extraer_contenido_seccion(h2_titulo):
    """Extrae contenido estructurado de una sección a partir de su título h2."""
    contenido_seccion = []
    
    # Buscar todos los elementos hermanos hasta el siguiente h2
    for elemento in h2_titulo.find_next_siblings():
        if elemento.name == 'h2':
            break
        
        # Manejar párrafos
        if elemento.name == 'p':
            texto = elemento.get_text(strip=True)
            if texto and not any(x in texto.lower() for x in ['mayo clinic', 'advertisement', 'anuncio']):
                contenido_seccion.append({
                    "tipo": "parrafo",
                    "contenido": texto
                })
        
        # Manejar listas
        elif elemento.name == 'ul':
            items_lista = []
            for li in elemento.find_all('li', recursive=False):
                texto_li = li.get_text(strip=True)
                if texto_li:
                    items_lista.append(texto_li)
            
            if items_lista:
                contenido_seccion.append({
                    "tipo": "lista",
                    "items": items_lista
                })
        
        # Manejar subtítulos h3
        elif elemento.name == 'h3':
            texto_titulo = elemento.get_text(strip=True)
            if texto_titulo:
                contenido_seccion.append({
                    "tipo": "subtitulo",
                    "contenido": texto_titulo
                })
        
        # Manejar elementos contenedores
        elif elemento.name in ['div', 'section']:
            # Excluir contenedores de anuncios
            if elemento.get('class') and any(cls in str(elemento.get('class')) 
                                           for cls in ['mayoad', 'ad-container', 'contentbox']):
                continue
                
            # Extraer párrafos dentro del contenedor
            for p in elemento.find_all('p', recursive=False):
                texto = p.get_text(strip=True)
                if texto and not any(x in texto.lower() for x in ['mayo clinic', 'advertisement']):
                    contenido_seccion.append({
                        "tipo": "parrafo", 
                        "contenido": texto
                    })
            
            # Extraer listas dentro del contenedor
            for ul in elemento.find_all('ul', recursive=False):
                items_lista = []
                for li in ul.find_all('li', recursive=False):
                    texto_li = li.get_text(strip=True)
                    if texto_li:
                        items_lista.append(texto_li)
                
                if items_lista:
                    contenido_seccion.append({
                        "tipo": "lista",
                        "items": items_lista
                    })
    
    return contenido_seccion

def extraer_secciones_pagina(soup, secciones_a_buscar):
    """Extrae las secciones específicas de una página."""
    secciones_extraidas = []
    
    for titulo_seccion in secciones_a_buscar:
        # Buscar h2 que contenga el texto de la sección
        h2_titulo = soup.find('h2', string=lambda text: text and titulo_seccion in text.lower())
        
        if h2_titulo:
            titulo_real = h2_titulo.get_text(strip=True)
            print(f"        -> Encontrada sección: '{titulo_real}'")
            
            contenido_seccion = extraer_contenido_seccion(h2_titulo)
            
            secciones_extraidas.append({
                "titulo": titulo_real,
                "contenido": contenido_seccion
            })
        else:
            print(f"        -> Sección '{titulo_seccion}' no encontrada")
    
    return secciones_extraidas

def extraer_departamentos(soup):
    """Extrae los nombres de los departamentos y especialidades."""
    departamentos = []
    
    try:
        # Buscar enlaces que probablemente sean departamentos
        enlaces = soup.find_all('a', href=True)
        
        for enlace in enlaces:
            texto = enlace.get_text(strip=True)
            # Filtrar enlaces que parecen ser departamentos o servicios
            if (len(texto) > 10 and 
                any(palabra in texto.lower() for palabra in ['servicio', 'departamento', 'clínica', 'especialidad', 'centro', 'hospital']) and
                not any(excluir in texto.lower() for excluir in ['facebook', 'twitter', 'youtube', 'linkedin', 'instagram', 'mayo clinic'])):
                
                if texto not in departamentos:
                    departamentos.append(texto)
                    print(f"        -> Encontrado departamento: '{texto}'")
        
        # Buscar en listas específicas
        listas = soup.find_all('ul')
        for lista in listas:
            for li in lista.find_all('li'):
                texto_li = li.get_text(strip=True)
                if texto_li and len(texto_li) > 10:
                    # Buscar texto de enlaces dentro del li
                    enlace_li = li.find('a')
                    if enlace_li:
                        texto_dep = enlace_li.get_text(strip=True)
                        if (texto_dep and texto_dep not in departamentos and
                            any(palabra in texto_dep.lower() for palabra in ['servicio', 'departamento', 'clínica'])):
                            departamentos.append(texto_dep)
                            print(f"        -> Encontrado departamento: '{texto_dep}'")
    
    except Exception as e:
        print(f"        -> ERROR al extraer departamentos: {e}")
    
    return departamentos

def extraer_detalles_completos(driver, url_enfermedad):
    """Extrae detalles completos de la enfermedad navegando por todas las pestañas."""
    resultados = {
        "sintomas_causas": [],
        "diagnostico_tratamiento": [],
        "departamentos": []
    }
    
    try:
        # 1. Página principal (Síntomas y causas)
        driver.get(url_enfermedad)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
        
        soup_principal = BeautifulSoup(driver.page_source, 'html.parser')
        resultados["sintomas_causas"] = extraer_secciones_pagina(soup_principal, SECCIONES_SINTOMAS_CAUSAS)
        
        # 2. Diagnóstico y tratamiento
        if hacer_clic_pestana(driver, "Diagnóstico y tratamiento"):
            soup_diagnostico = BeautifulSoup(driver.page_source, 'html.parser')
            resultados["diagnostico_tratamiento"] = extraer_secciones_pagina(soup_diagnostico, SECCIONES_DIAGNOSTICO_TRATAMIENTO)
        
        # 3. Médicos y departamentos
        if hacer_clic_pestana(driver, "Médicos y departamentos"):
            soup_departamentos = BeautifulSoup(driver.page_source, 'html.parser')
            departamentos = extraer_departamentos(soup_departamentos)
            resultados["departamentos"] = departamentos
        
    except TimeoutException:
        print(f"      -> ERROR: La página {url_enfermedad} no cargó a tiempo.")
    except Exception as e:
        print(f"      -> ERROR: Ocurrió un error inesperado al procesar {url_enfermedad}: {e}")
    
    return resultados

if __name__ == "__main__":
    """
    Proceso principal para extraer detalles de enfermedades desde un archivo JSON de entrada.
    1. Cargar la lista de enfermedades desde un archivo JSON.
    2. Iniciar el navegador Selenium.
    3. Procesar cada enfermedad para extraer detalles.
    4. Cerrar el navegador.
    5. Guardar el resultado final en un archivo JSON.
    """
    try:
        with open(ARCHIVO_ENTRADA, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        lista_enfermedades = datos.get("enfermedades", [])
        print(f"Se cargaron {len(lista_enfermedades)} enfermedades del archivo '{ARCHIVO_ENTRADA}'.")
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de entrada '{ARCHIVO_ENTRADA}'.")
        exit()
    except json.JSONDecodeError:
        print(f"Error: El archivo '{ARCHIVO_ENTRADA}' no es un JSON válido.")
        exit()

    # --- 2. Iniciar el navegador ---
    service = Service()
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(service=service, options=options)
    
    print("\nNavegador Chrome iniciado. Comenzando extracción de detalles...")
    print(f"Secciones a extraer:")
    print(f"  - Síntomas y causas: {', '.join(SECCIONES_SINTOMAS_CAUSAS)}")
    print(f"  - Diagnóstico y tratamiento: {', '.join(SECCIONES_DIAGNOSTICO_TRATAMIENTO)}")
    print(f"  - Médicos y departamentos: Nombres de departamentos y especialidades")

    enfermedades_con_detalles = []
    total = len(lista_enfermedades)

    # --- 3. Procesar cada enfermedad ---
    for i, enfermedad in enumerate(lista_enfermedades):
        print(f"\n({i+1}/{total}) Procesando: {enfermedad.get('nombre', 'Nombre Desconocido')}")
        print(f"   URL: {enfermedad.get('url')}")
        
        detalles = extraer_detalles_completos(driver, enfermedad.get('url'))
        
        # Combinar todos los detalles
        enfermedad.update(detalles)
        enfermedades_con_detalles.append(enfermedad)
        
        # Pausa para no sobrecargar el servidor
        time.sleep(2)

    # --- 4. Cerrar el navegador ---
    print("\nExtracción de detalles finalizada. Cerrando el navegador.")
    driver.quit()

    # --- 5. Guardar el resultado final ---
    datos_finales = {
        "metadata": {
            "fuente": datos.get("metadata", {}).get("fuente"),
            "total_registros": len(enfermedades_con_detalles),
        },
        "enfermedades": enfermedades_con_detalles
    }

    with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
        json.dump(datos_finales, f, ensure_ascii=False, indent=4)

    print("\n" + "="*60)
    print("¡Proceso completado con éxito!")
    print(f"Los datos completos se han guardado en '{ARCHIVO_SALIDA}'")
    print("="*60)