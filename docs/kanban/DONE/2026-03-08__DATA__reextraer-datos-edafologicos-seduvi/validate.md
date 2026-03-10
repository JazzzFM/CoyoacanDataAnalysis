# Validation

## Commands
```sql
SELECT COUNT(*) AS total FROM datos_edafologicos_particionada;
-- Esperado: ~1,979 manzanas con uso de suelo

SELECT "USO_SUELO", COUNT(*) FROM datos_edafologicos_particionada GROUP BY 1 ORDER BY 2 DESC;

SELECT COUNT(*), ST_IsValid("GEOM_MANZANA") FROM datos_edafologicos_particionada GROUP BY 2;
```

## Results
- PASS/FAIL: Pendiente

## Notes
- Pendiente de ejecución
