# Validation

## Commands
```sql
SELECT COUNT(*) AS total FROM datos_demograficos_particionada;
SELECT DISTINCT anio FROM datos_demograficos_particionada;
SELECT COUNT(*), ST_IsValid(geometry) FROM datos_demograficos_particionada GROUP BY 2;
SELECT MIN(pob_total), MAX(pob_total), AVG(pob_total)::int FROM datos_demograficos_particionada;
SELECT MIN(densidad_pob_total), MAX(densidad_pob_total) FROM datos_demograficos_particionada WHERE densidad_pob_total > 0;
```

## Results
- PASS/FAIL: Pendiente

## Notes
- Pendiente de ejecución
