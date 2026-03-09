# Diccionario de Datos

Catálogo de todas las columnas, tablas y fuentes de datos del proyecto Coyoacán Data Analysis.

---

## Tablas PostGIS

### `poligonos_manzanas_agebs_colonias`

Tabla maestra de polígonos geográficos. Contiene la jerarquía geográfica completa a tres niveles de granularidad. Se usa como tabla base para hacer merge con datos temáticos.

| Columna | Tipo | Descripción |
|---|---|---|
| GID_MANZANA | integer | Identificador único de manzana (PK) |
| ID_MANZANA | string | Código de manzana |
| GEOM_MANZANA | geometry | Polígono de la manzana |
| GID_AGEB | integer | Identificador único de AGEB |
| ID_AGEB | string | Código AGEB (4 dígitos) |
| GEOM_AGEB | geometry | Polígono del AGEB |
| ID_COLONIA | integer | Identificador de colonia |
| NOMBRE_COLONIA | string | Nombre de la colonia |
| GEOM_COLONIA | geometry | Polígono de la colonia |

### `datos_demograficos_particionada`

Datos del censo de población INEGI 2020 a nivel AGEB. 154 registros correspondientes a los AGEBs de Coyoacán.

**Fuente:** INEGI Censo de Población y Vivienda 2020
**CRS original:** EPSG:32614 (UTM Zona 14N), almacenado en EPSG:4326

#### Columnas de identificación

| Columna | Tipo | Descripción |
|---|---|---|
| ageb | string | Código AGEB completo (CVEGEO, 13 dígitos). Clave de merge con `ID_AGEB` de la tabla de polígonos |
| alc | string | Nombre de alcaldía ("Coyoacán") |
| loc | string | Tipo de localidad ("Urbana") |
| amb_loc | string | Código de ámbito de localidad |
| anio | integer | Año del censo (2020) |
| territorio | string | Identificador de territorio ("coyoacan") |
| geometry | geometry | Polígono AGEB en EPSG:4326 |

#### Columnas de población absoluta (prefijo `p_` o `pob_`)

| Columna | Tipo | Descripción |
|---|---|---|
| pob_total | integer | Población total |
| pob_hombres | integer | Población masculina |
| pob_mujeres | integer | Población femenina |
| p_3ymas | integer | Población de 3 años y más |
| p_12yms | integer | Población de 12 años y más |
| p_nacoe | integer | Población nacida en otra entidad |
| p_vivoe | integer | Población que vivía en otra entidad hace 5 años |
| p_hli | integer | Hablantes de lengua indígena |
| p_hl_nh | integer | Hablantes de lengua indígena (solo español) |
| p_hli_h | integer | Hablantes de lengua indígena (bilingües) |
| p_afrmx | integer | Población afromexicana |
| p_p12ym_sl | integer | Población 12+ sin escolaridad |
| p_p12ym_c | integer | Población 12+ con educación completa |
| p_p12ym_sp | integer | Población 12+ con educación incompleta |
| p_catlc | integer | Población que asiste a la escuela |
| p_criev | integer | Población con registro civil |
| p_trsrl | integer | Población con transporte |
| p_sinrl | integer | Población sin registro civil |

#### Columnas de tasas/porcentajes (prefijo `t_`)

| Columna | Tipo | Descripción |
|---|---|---|
| t_nacoe | float | % población nacida en otra entidad |
| t_vivoe | float | % población que vivía en otra entidad hace 5 años |
| t_hli | float | % hablantes de lengua indígena |
| t_hl_nh | float | % hablantes indígenas solo español |
| t_hli_h | float | % hablantes indígenas bilingües |
| t_afrmx | float | % población afromexicana |
| t_p12ym_sl | float | % población 12+ sin escolaridad |
| t_p12ym_c | float | % población 12+ con educación completa |
| t_p12ym_sp | float | % población 12+ con educación incompleta |
| t_catlc | float | % población que asiste a la escuela |
| t_criev | float | % población con registro civil |
| t_trsrl | float | % población con transporte |
| t_sinrl | float | % población sin registro civil |

#### Columnas calculadas (derivadas en notebooks)

| Columna | Tipo | Descripción | Fórmula |
|---|---|---|---|
| area_km2 | float | Área en km² | `geometry.area / 10^6` (en UTM) |
| densidad_pob_total | float | Densidad de población (hab/km²) | `pob_total / area_km2` |
| densidad_hombres | float | Densidad masculina (hab/km²) | `pob_hombres / area_km2` |
| densidad_mujeres | float | Densidad femenina (hab/km²) | `pob_mujeres / area_km2` |
| relacion_genero | float | Razón densidad masculina/femenina | `densidad_hombres / densidad_mujeres` |
| dependencia_infantil | float | Razón de dependencia infantil | Derivada de columnas de edad |

### `datos_edafologicos_particionada`

Datos de uso de suelo a nivel manzana. 1,979 registros.

**Fuente:** SEDUVI (Secretaría de Desarrollo Urbano y Vivienda), datos de uso de suelo 2017
**CRS:** EPSG:4326

| Columna | Tipo | Descripción |
|---|---|---|
| ID_MANZANA | string | Código de manzana. Clave de merge con tabla de polígonos |
| GEOM_MANZANA | geometry | Polígono de la manzana |
| USO_SUELO | string | Categoría de uso de suelo (ver tabla de valores abajo) |
| SUPERFICIE | float | Superficie del predio en m² |
| DNSDD_D | string | Descripción de densidad (ej: "Baja 1 viv/100 m2") |
| NIVELES | float | Número de niveles/pisos del edificio |
| ALTURA | float | Altura del edificio en metros |
| are_lbr | float | Área libre en m² |
| mnm_vvn | float | Tamaño mínimo de vivienda |
| anio | string | Año del dato (2017) |
| territorio | string | Identificador de territorio ("coyoacan") |
| ID_AGEB | string | Código AGEB asociado |
| NOMBRE_COLONIA | string | Nombre de la colonia |
| ID_COLONIA | integer | Identificador de colonia |

#### Valores de `USO_SUELO`

| Valor | Descripción |
|---|---|
| Habitacional | Uso residencial general |
| Habitacional con Comercio en Planta Baja | Mixto: vivienda con comercio abajo |
| Habitacional Unifamiliar | Vivienda unifamiliar |
| Habitacional Unifamiliar y/o Plurifamiliar | Vivienda mixta |
| Habitacional Mixto | Uso residencial mixto |
| Centro de Barrio | Centro comercial/social de barrio |
| Equipamiento | Equipamiento urbano (escuelas, hospitales, etc.) |
| Equipamiento de Servicios | Equipamiento de servicios públicos |
| Espacios Abiertos | Parques, plazas, áreas verdes |
| Sin Zonificación | Sin clasificación asignada |
| Sin Datos | Manzanas sin información de uso de suelo |

### `users`

Tabla de autenticación de la aplicación Flask.

| Columna | Tipo | Descripción |
|---|---|---|
| id | integer | Clave primaria |
| username | string(64) | Nombre de usuario, único |
| password_hash | string(128) | Hash de contraseña (werkzeug) |

---

## Fuentes de Datos

| Fuente | Año | Proveedor | Nivel | Formato Original |
|---|---|---|---|---|
| Censo de Población y Vivienda | 2020 | INEGI | AGEB | Shapefile |
| DENUE (Directorio Nacional de Unidades Económicas) | 2010 | INEGI | Punto | Shapefile |
| Uso de Suelo | 2017 | SEDUVI | Predio/Punto | Shapefile |
| Límites de Alcaldías CDMX | Vigente | INEGI | Municipio | Shapefile |
| Manzanas Urbanas | Vigente | INEGI | Manzana | Shapefile |
| Colonias Coyoacán | Vigente | INEGI | Colonia | Shapefile |
| AGEBs Urbanas CDMX | Vigente | INEGI | AGEB | Shapefile |

---

## Sistemas de Coordenadas (CRS)

| CRS | Código | Uso | Notas |
|---|---|---|---|
| WGS84 | EPSG:4326 | Almacenamiento y visualización | Sistema estándar lat/lon |
| UTM Zona 14N | EPSG:32614 | Cálculos de área en m²/km² | Proyección métrica para CDMX |
| Lambert Conformal Conic | Mexico-specific | CRS original de datos DENUE | Se convierte a 4326 en ingesta |

---

## Rutas de Datos Fuente

```
data/
├── demografico/2020/       # hombres.shp, mujeres.shp, total.shp
├── limites/                # poligonos_alcaldias_cdmx.shp
├── manzanas/               # 090030001m.shp
├── uso_suelo/              # uso-de-suelo.shp
├── colonias/               # colonias_coyoacan.shp
└── economicos/             # DENUE shapefile

clean_data/poligonos/       # Datos limpios post-procesamiento
├── manzana/                # manzanas_coyoacan_clean.*
├── ageb/                   # ageb_coyoacan_clean.*
├── colonia/                # colonias_coyoacan_clean.*
└── municipio/              # municipio_coyoacan_clean.*
```
