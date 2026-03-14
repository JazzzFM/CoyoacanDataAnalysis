---
id: "TASK-2026-03-09__analisis-accesibilidad"
title: "Análisis de accesibilidad a servicios (desiertos urbanos)"
status: "DONE"
phase: "Validate"
scope_in:
  - "Calcular distancia de cada manzana al servicio más cercano (salud, educación, comercio)"
  - "Generar buffers/isócronas de 5/10/15 min caminando (400m/800m/1200m)"
  - "Identificar desiertos urbanos: zonas sin servicio en radio de 15 min"
  - "Mapa de calor de accesibilidad por categoría de servicio"
  - "Usar ST_Distance, ST_Buffer de PostGIS"
scope_out:
  - "Isócronas reales con red vial (requiere OSRM o similar)"
  - "Análisis de capacidad de los servicios"
artifacts:
  card: card.md
plan_phase: 3
---

# Summary
- Objective: Responder "¿A cuántos metros está el servicio más cercano de cada zona de Coyoacán?" e identificar desiertos urbanos donde los ciudadanos no tienen acceso.
- Constraints: Isócronas simplificadas (buffer circular, no red vial real). Requiere DENUE cargado.

# Metodología
1. Para cada manzana, calcular `ST_Distance(centroide_manzana, punto_servicio_más_cercano)` en metros
2. Clasificar accesibilidad:
   - < 400m (5 min): Alta
   - 400-800m (10 min): Media
   - 800-1200m (15 min): Baja
   - > 1200m: Desierto urbano
3. Generar mapas por categoría de servicio (salud, educación, alimentación)
4. Cruzar con densidad poblacional: desiertos + alta densidad = máxima urgencia

# Análisis espacial PostGIS
```sql
-- Ejemplo: distancia al centro de salud más cercano por manzana
SELECT m."ID_MANZANA",
       MIN(ST_Distance(
           ST_Transform(m."GEOM_MANZANA", 32614),
           ST_Transform(s.geometry, 32614)
       )) AS dist_salud_m
FROM poligonos_manzanas_agebs_colonias m
CROSS JOIN LATERAL (
    SELECT geometry FROM datos_servicios
    WHERE categoria = 'salud'
    ORDER BY m."GEOM_MANZANA" <-> geometry
    LIMIT 1
) s
GROUP BY m."ID_MANZANA";
```

# Usuarios objetivo
- **Investigador:** Publica análisis de accesibilidad con evidencia cuantitativa
- **Funcionario:** Identifica dónde faltan servicios y prioriza construcción
- **Ciudadano:** Ve si su zona tiene acceso adecuado a servicios

# Dependencias
- **Requiere:** DATA__cargar-datos-denue
- **Requiere:** REFACTOR__unificar-apps-dash
- **Bloquea:** TASK__indice-vulnerabilidad (componente de accesibilidad)

# Updates
- 2026-03-09 - Created.
- 2026-03-14 - Implementado como /dashboard/accesibilidad. Usa nearest-neighbor con GeoPandas/Shapely en vez de PostGIS ST_Distance (datos ya en memoria). Granularidad por colonia (no manzana). 9 categorías DENUE. Commit 4d937e3.
