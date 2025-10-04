# Sistema Experto para Pre-Diagnóstico Médico.

Este proyecto es un sistema experto basado en inteligencia artificial diseñado para ofrecer orientación sobre posibles diagnósticos médicos. El usuario puede describir sus síntomas en lenguaje natural y el sistema utiliza técnicas de búsqueda semántica y resumen de texto para presentar las enfermedades más relevantes de su base de conocimiento.

## Características Principales

-   **Búsqueda Semántica de Síntomas**: Utiliza modelos de `sentence-transformers` para entender el significado detrás de la descripción del usuario, en lugar de solo buscar palabras clave.
-   **Resúmenes con IA**: Emplea modelos de `transformers` para generar resúmenes concisos de la descripción, diagnóstico y tratamiento de cada enfermedad.
-   **Interfaz Interactiva**: Construido con Streamlit para una experiencia de usuario amigable y reactiva.
-   **Pipeline de Datos Automatizado**: Incluye una serie de scripts para construir la base de conocimiento desde cero, empezando por web scraping con Selenium.

##  Flujo del Proyecto y Estructura de Archivos

El proyecto se divide en dos fases principales: la **preparación de datos** (un pipeline de 4 pasos) y la **aplicación interactiva**.

### Diagrama del Pipeline de Datos

```
[Web Scraping] -> 1_scrape_lista_enfermedades.py -> [1_....json]
                                                         |
                                                         v
[Web Scraping] -> 2_scrape_detalles_enfermedades.py -> [2_....json]
                                                          |
                                                          v
[Procesamiento] -> 3_procesar_y_enriquecer_datos.py -> [3_....json]
                                                           |
                                                           v
[Embeddings] -> 4_preparar_embeddings.py -> [app_data.pkl | app_embeddings.pt]
                                                              |
                                                              v
                                                        [Aplicación] -> UI.py
```

### Descripción de Archivos

-   **Scripts del Pipeline de Datos (`1` al `4`)**:
    -   `1_scrape_lista_enfermedades.py`: Extrae la lista inicial de enfermedades y sus URLs.
    -   `2_scrape_detalles_enfermedades.py`: Visita cada URL para extraer los detalles completos (síntomas, causas, etc.).
    -   `3_procesar_y_enriquecer_datos.py`: Limpia y procesa los datos crudos usando `spaCy`.
    -   `4_preparar_embeddings.py`: Genera los vectores semánticos (embeddings) y los guarda en archivos optimizados para la app.
-   **Aplicación Principal**:
    -   `UI.py`: La aplicación de Streamlit que el usuario final utiliza.
-   **Configuración de Docker**:
    -   `Dockerfile`: Instrucciones para construir la imagen de la aplicación.
    -   `requirements.txt`: Lista de dependencias de Python.

##  Cómo Ejecutar el Proyecto

La manera de ejecutar la aplicación: Es de forma local.

Compartimos el link de la versión de Python para la ejecución del código, para no llegar a tener incompatibilidades con el entorno virtual https://www.python.org/downloads/release/python-3119/   

### Ejecución Local

1.  **Clonar el repositorio**:
    ```bash
    git clone https://github.com/JuanFranciscoRamosChavez/Sistema-Experto.git
    cd Sistema-Experto
    ```

2.  **Crear y activar un entorno virtual**:
    ```bash
    # Crear el entorno
    py -3.11 -m venv .venv

    # Activar en Windows
    .\.venv\Scripts\activate

    # Activar en macOS/Linux
    source .venv/bin/activate
    ```

3.  **Instalar las dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Ejecutar el pipeline de datos (si es la primera vez)**:
    *Debes ejecutar los scripts en orden para generar los archivos `app_data.pkl` y `app_embeddings.pt`.*
    ```bash
    python 1_scrape_lista_enfermedades.py
    python 2_scrape_detalles_enfermedades.py
    python 3_procesar_y_enriquecer_datos.py
    python 4_preparar_embeddings.py
    ```

5.  **Ejecutar la aplicación**:
    ```bash
    streamlit run UI.py
    ```

##  Tecnologías Utilizadas

-   **Python**
-   **Streamlit**: Para la interfaz de usuario.
-   **Hugging Face Transformers**: Para los modelos de búsqueda semántica y resumen de texto.
-   **spaCy**: Para el procesamiento de lenguaje natural en el pipeline.
-   **Selenium**: Para el web scraping.
-   **Pandas**: Para la manipulación de datos.
