# Coyoacán Data Analysis

## Descripción del Proyecto

Este proyecto tiene como objetivo realizar un análisis detallado de la alcaldía de Coyoacán, utilizando datos georreferenciados, económicos, electorales, y ambientales para identificar patrones y necesidades específicas de la comunidad. Este análisis está diseñado para proporcionar información valiosa que pueda guiar la toma de decisiones estratégicas, especialmente en contextos políticos y de políticas públicas.

## Objetivos del Análisis

1. **Evaluar la Demografía y Economía Local**: Analizar la distribución de la población, ingresos, empleo, y otros indicadores económicos clave para identificar áreas con alta vulnerabilidad o potencial de crecimiento.

2. **Estudiar la Accesibilidad a Servicios Públicos**: Mapear la accesibilidad a servicios de salud, educación, y transporte para identificar brechas y proponer mejoras en la infraestructura pública.

3. **Analizar la Calidad Ambiental y Recursos Naturales**: Evaluar la calidad del aire, acceso a áreas verdes, y otros indicadores ambientales, correlacionándolos con la salud pública y la calidad de vida.

4. **Explorar Patrones Electorales**: Integrar datos electorales para entender cómo las características demográficas y económicas influyen en los resultados de las elecciones locales.

5. **Proponer Recomendaciones Estratégicas**: Basado en los hallazgos, sugerir intervenciones y políticas públicas que mejoren la calidad de vida en Coyoacán, enfocándose en los grupos más vulnerables y en áreas con mayores necesidades.

6. Migración a PostGIS
   - Objetivo: Migrar los datos geoespaciales desde archivos shapefile (SHP) a una base de datos PostgreSQL con extensión PostGIS.
   - Funcionalidades: Permitir consultas eficientes de datos georreferenciados mediante índices espaciales y funcionalidades avanzadas de PostGIS.
   - Pasos:
     - Configuración de la base de datos en PostgreSQL con soporte PostGIS.
     - Ingesta de los archivos SHP utilizando herramientas como `ogr2ogr`.
     - Verificación de integridad y calidad de los datos importados.
     - Configuración de seguridad y acceso mediante variables de entorno definidas en un archivo `.env`.

7. Creación de un Dashboard con Dash
   - Objetivo: Crear un dashboard interactivo utilizando Dash que permita visualizar y analizar los datos geoespaciales de Coyoacán.
   - Funcionalidades: Visualización de mapas, gráficos y otros análisis exploratorios que se integren a lo largo del proyecto.
   - Pasos:
     - Desarrollo de la aplicación Dash en Python.
     - Integración con la base de datos PostGIS para consulta de datos en tiempo real.
     - Despliegue en un contenedor Docker, con configuración para estar en la misma red interna que el servicio de PostGIS.


## Plan para Importar y Organizar Datos Georreferenciados de Coyoacán


### Definir los Datos Necesarios

- **Datos de Suelos**: Información edafológica de Coyoacán (calidad del suelo, uso del suelo, etc.).
- **Datos Demográficos**: Población, densidad, ingresos, educación.
- **Datos de Infraestructura**: Ubicación de servicios públicos (escuelas, hospitales, transporte).
- **Datos Ambientales**: Calidad del aire, áreas verdes, fuentes de agua.

## Estructura de Carpeta para los Datos

Organiza tus datos en carpetas para mantener todo ordenado:

```bash
mkdir -p Coyoacan_Analysis/data/{edafologia,demografia,infraestructura,ambientales}
```

## Descarga y Verificación de Datos

Para cada tipo de dato, descarga desde fuentes confiables y verifica que los archivos sean correctos (formato, integridad).

## Estructura del Proyecto

El proyecto está organizado de la siguiente manera:

```
Coyoacan_Analysis/
│
├── data/                         # Carpeta para almacenar todos los datos descargados
│   ├── economicos/               # Subcarpeta para datos económicos
│   ├── electorales/              # Subcarpeta para datos electorales
│   ├── georeferenciados/         # Subcarpeta para datos georreferenciados
│   └── naturales/                # Subcarpeta para datos de recursos naturales
│
├── scripts/                      # Carpeta para scripts de Python
│   ├── data_cleaning.py          # Script para limpieza y preparación de datos
│   ├── analysis.py               # Script principal de análisis
│   ├── visualizations.py         # Script para crear visualizaciones
│   └── compile_report.py         # Script para compilar las visualizaciones en PDF
│
├── outputs/                      # Carpeta para resultados y productos finales
│   ├── figures/                  # Subcarpeta para figuras generadas
│   └── reports/                  # Subcarpeta para reportes en PDF
│
└── README.md                     # Documento para describir el proyecto y cómo ejecutarlo
```

## Requisitos

- Python 3.x
- Bibliotecas: `pandas`, `geopandas`, `matplotlib`, `seaborn`, `plotly`, `dash`, `scikit-learn`

Para instalar las dependencias, ejecuta:

```bash
pip install -r requirements.txt
```

## Uso

1. **Limpieza de Datos**: Ejecuta `data_cleaning.py` para procesar y limpiar los datos brutos.

2. **Análisis de Datos**: Ejecuta `analysis.py` para realizar el análisis exploratorio y avanzado, incluyendo correlaciones, clustering, y modelos predictivos.

3. **Generación de Visualizaciones**: Ejecuta `visualizations.py` para crear gráficos y mapas interactivos que resumen los hallazgos clave.

4. **Compilación del Reporte**: Ejecuta `compile_report.py` para compilar todas las visualizaciones y resultados en un reporte en PDF.


## Arquitectura del Proyecto
El proyecto está compuesto por los siguientes componentes principales:

1. Base de Datos PostGIS:
   - Almacena todos los datos geoespaciales y permite realizar consultas eficientes.
   - Contenedor Docker con PostgreSQL y extensión PostGIS.

2. API y Dashboard:
   - Aplicación desarrollada en Dash para la visualización y análisis de los datos.
   - Se comunica directamente con la base de datos PostGIS.
   - Contenedor Docker separado, pero en la misma red que PostGIS.

3. Red y Seguridad:
   - Los contenedores estarán bajo la misma red Docker para comunicación segura y eficiente.
   - Uso de archivos `.env` para gestionar credenciales y configuraciones sensibles, los cuales están listados en el `.gitignore` para evitar exposición.

## Instalación y Configuración
1. Clona el repositorio y navega a la carpeta del proyecto:
2. Configura las variables de entorno:
- Crea un archivo `.env` en la raíz del proyecto basado en el `.env.example`.
- Asegúrate de definir las credenciales para la base de datos, secretos y configuraciones de red.

3. Construye y levanta los contenedores:
	
	docker-compose up --build


## Contribuciones

Este proyecto es colaborativo y abierto a sugerencias y mejoras. Para contribuir, por favor sigue los siguientes pasos:

1. Forkea el repositorio.
2. Crea una rama (`feature/nueva-caracteristica`).
3. Haz commit de tus cambios (`git commit -am 'Añadir nueva característica'`).
4. Haz push a la rama (`git push origin feature/nueva-caracteristica`).
5. Abre un Pull Request.

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE.md para más detalles.
