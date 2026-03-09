# Validation

## Commands

### Base de datos (Neon)
```sql
-- PostGIS habilitado
SELECT PostGIS_version();

-- Tablas migradas con conteos correctos
SELECT 'poligonos' AS tabla, COUNT(*) FROM poligonos_manzanas_agebs_colonias
UNION ALL
SELECT 'demograficos', COUNT(*) FROM datos_demograficos_particionada
UNION ALL
SELECT 'edafologicos', COUNT(*) FROM datos_edafologicos_particionada;

-- Geometrías válidas
SELECT COUNT(*), ST_IsValid("GEOM_MANZANA") FROM poligonos_manzanas_agebs_colonias GROUP BY 2;

-- Años disponibles
SELECT DISTINCT anio FROM datos_demograficos_particionada ORDER BY 1;
```

### Aplicación (Render)
```bash
# App responde
curl -I https://<app-name>.onrender.com/

# Dashboard renderiza
curl -s https://<app-name>.onrender.com/dashboard/ | grep -c "Coyoacán"
```

### Conexión app → DB
```python
# Test local contra Neon
from sqlalchemy import create_engine, text
engine = create_engine("postgresql://...@xyz.neon.tech/Poligonos?sslmode=require")
with engine.connect() as conn:
    result = conn.execute(text("SELECT PostGIS_version()"))
    print(result.fetchone())
```

## Results
- PASS/FAIL: Pendiente

## Checklist
- [ ] PostGIS habilitado en Neon
- [ ] 3 tablas migradas con conteos correctos
- [ ] Geometrías válidas (0 inválidas)
- [ ] App responde en URL de Render
- [ ] Mapa manzana renderiza
- [ ] Mapa AGEB renderiza
- [ ] Mapa colonia renderiza
- [ ] Dropdown de métricas se puebla
- [ ] Storage Neon < 500 MB
- [ ] UptimeRobot configurado

## Notes
- Pendiente de ejecución
