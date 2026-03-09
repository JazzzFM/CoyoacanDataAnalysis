# Validation

## Commands
```sql
-- Conteo total
SELECT COUNT(*) AS total FROM poligonos_manzanas_agebs_colonias;

-- Geometrías válidas por nivel
SELECT 'MANZANA' AS nivel, COUNT(*), SUM(CASE WHEN ST_IsValid("GEOM_MANZANA") THEN 1 ELSE 0 END) AS validas FROM poligonos_manzanas_agebs_colonias
UNION ALL
SELECT 'AGEB', COUNT(*), SUM(CASE WHEN ST_IsValid("GEOM_AGEB") THEN 1 ELSE 0 END) FROM poligonos_manzanas_agebs_colonias
UNION ALL
SELECT 'COLONIA', COUNT(*), SUM(CASE WHEN ST_IsValid("GEOM_COLONIA") THEN 1 ELSE 0 END) FROM poligonos_manzanas_agebs_colonias;

-- Distintos por nivel
SELECT COUNT(DISTINCT "ID_AGEB") AS agebs, COUNT(DISTINCT "ID_COLONIA") AS colonias FROM poligonos_manzanas_agebs_colonias;

-- Manzanas sin AGEB o colonia asignada
SELECT COUNT(*) AS huerfanas FROM poligonos_manzanas_agebs_colonias WHERE "ID_AGEB" IS NULL OR "ID_COLONIA" IS NULL;
```

## Results
- PASS/FAIL: Pendiente

## Notes
- Pendiente de ejecución
