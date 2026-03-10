# Research: Ingesta de datos abiertos CDMX

## Portales investigados

### datos.cdmx.gob.mx (FUENTE PRINCIPAL)
- **247 datasets SHP**, 119 GeoJSON disponibles
- Licencia: Creative Commons Attribution 4.0
- Cobertura: toda la CDMX, filtrable/recortable a Coyoacán
- Formatos: SHP (principal), GeoJSON, KMZ, CSV
- Mantenimiento: activo, actualizaciones frecuentes

### datamx.io
- 142 datasets SHP total
- **Mayormente datos de Jalisco/Guadalajara** (IMEPLANAMG)
- Pocos datasets útiles para Coyoacán
- **Veredicto: NO productivo para este proyecto**

### datos.gob.mx
- 95 datasets SHP de nivel nacional
- Fuentes: CONAPO, CONEVAL, SEPOMEX, CONANP
- Útil para índices de marginación y rezago social
- Requiere recorte a CDMX/Coyoacán

## Notas técnicas para ETL

### Patrón general de procesamiento
1. Descargar SHP desde portal
2. Cargar con `gpd.read_file()`
3. Verificar CRS (la mayoría viene en EPSG:4326 o EPSG:32614)
4. Filtrar a Coyoacán:
   - Por atributo: columna alcaldía/demarcación/municipio
   - Por spatial clip: `gpd.clip(gdf, poligono_coyoacan)`
   - Por spatial join: `gpd.sjoin(gdf, gdf_coyoacan)`
5. Reproyectar si es necesario a EPSG:4326
6. Subir a PostGIS con `gdf.to_postgis()`

### Datasets por colonia vs por AGEB vs puntuales
- **Por colonia:** Valor suelo, violencia, zonificación sísmica, agua, áreas verdes
  - Merge directo con `poligonos_colonia` por nombre de colonia
- **Por AGEB:** Inundaciones, internet, algunos demográficos
  - Merge con `poligonos_ageb` por clave AGEB
- **Puntuales:** Metro, hospitales, escuelas, tianguis
  - Spatial join con polígonos para asignar a colonia/AGEB
  - O mostrar como capa de puntos superpuesta

### Granularidad por rubro

| Rubro | Nivel | Merge con |
|-------|-------|-----------|
| Gentrificación | Colonia | NOMBRE_COLONIA |
| Transporte | Puntos/líneas | Capa superpuesta |
| Seguridad | Colonia | NOMBRE_COLONIA |
| Medio ambiente | Colonia | NOMBRE_COLONIA |
| Infraestructura | Puntos | Spatial join |
| Economía | Colonia | NOMBRE_COLONIA |

### Tablas PostGIS sugeridas

```sql
-- Datos de gentrificación (por colonia)
datos_gentrificacion (colonia, valor_suelo_hab, valor_suelo_com,
    pct_viviendas_desocupadas, densidad_hab, incremento_pob,
    incremento_valor_viv, ue_turismo, anio, geometry)

-- Transporte (puntos y líneas)
datos_transporte_estaciones (nombre, sistema, linea, tipo, geometry)
datos_transporte_lineas (nombre, sistema, tipo, geometry)
datos_transporte_cobertura (sistema, radio_m, geometry)

-- Seguridad y riesgo (por colonia)
datos_seguridad (colonia, grado_marginalidad, grado_violencia,
    zona_sismica, riesgo_inundacion, riesgo_multi, anio, geometry)

-- Ambientales extendidos (por colonia)
datos_ambientales_ext (colonia, m2_espacio_publico_hab,
    rezago_espacio_publico, temp_nocturna, consumo_agua_bim,
    pct_deforestacion, geometry)

-- Equipamiento urbano (puntos)
datos_equipamiento (nombre, tipo, subtipo, geometry)
```

### Consideraciones de rendimiento
- Algunos datasets son grandes (CDMX completa). Filtrar ANTES de subir.
- Para capas de puntos (Metro, hospitales), considerar índice espacial.
- Dashboard: datasets por colonia se integran fácil al flujo actual.
  Capas de puntos requieren nueva lógica de visualización (scatter_mapbox).

## Datasets descartados
- datamx.io: casi todo es Jalisco
- Datasets sin geometría o solo PDF
- Datos que requieren acceso especial (INFOCDMX)
