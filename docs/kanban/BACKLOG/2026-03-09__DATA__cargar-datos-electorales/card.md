---
id: "DATA-2026-03-09__cargar-datos-electorales"
title: "Descargar y cargar datos electorales INE a Neon"
status: "BACKLOG"
phase: "Research"
scope_in:
  - "Descargar resultados electorales 2024 (o 2021) por sección electoral"
  - "Mapear secciones electorales a AGEBs/colonias de Coyoacán"
  - "Crear tabla datos_electorales en Neon PostGIS"
  - "Campos: participación, votos por partido, sección electoral"
  - "Crear script ETL en scripts/"
scope_out:
  - "Análisis predictivo electoral"
  - "Datos de encuestas"
artifacts:
  card: card.md
plan_phase: 1
---

# Summary
- Objective: Tener resultados electorales geolocalizados para correlacionar con perfil socioeconómico y demográfico de Coyoacán.
- Constraints: Datos del INE son públicos. Las secciones electorales no coinciden exactamente con AGEBs; se necesita un mapeo espacial.

# Fuente de datos
- **Resultados:** https://computos2024.ine.mx/publicacion/nacional/circunscripcion/5/local/9
- **Cartografía electoral:** https://cartografia.ine.mx/sige/descarga/
- **Formato:** CSV (resultados) + SHP (secciones electorales)

# Tabla destino
```sql
CREATE TABLE datos_electorales (
    id SERIAL PRIMARY KEY,
    seccion_electoral TEXT,
    lista_nominal INT,
    participacion FLOAT,
    votos_morena INT,
    votos_pan INT,
    votos_pri INT,
    votos_mc INT,
    votos_otros INT,
    votos_nulos INT,
    geometry GEOMETRY(POLYGON, 4326),
    anio INT,
    tipo_eleccion TEXT    -- presidencial, local, alcaldia
);
```

# Dependencias
- **Requiere:** Nada
- **Bloquea:** TASK__rubro-electoral

# Updates
- 2026-03-09 - Created. Datos INE de acceso público.
