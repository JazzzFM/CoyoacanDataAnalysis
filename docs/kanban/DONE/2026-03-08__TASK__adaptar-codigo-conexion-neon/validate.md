# Validation

## Commands
```bash
# Test conexión desde dashboard standalone
cd dashboard && python -c "
from data_access.data_connection import DatabaseCredentials, DatabaseConnectionManager
import os
creds = DatabaseCredentials(
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT', 5432)),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)
mgr = DatabaseConnectionManager(creds)
engine = mgr.get_engine()
from sqlalchemy import text
with engine.connect() as conn:
    r = conn.execute(text('SELECT COUNT(*) FROM poligonos_manzanas_agebs_colonias'))
    print(f'Registros: {r.fetchone()[0]}')
    print('Conexión OK')
"
```

## Checklist
- [ ] No hay credenciales hardcodeadas en el código
- [ ] `.env.example` creado con todas las variables
- [ ] Conexión a Neon funciona desde local
- [ ] `pool_pre_ping=True` configurado
- [ ] `sslmode=require` en connection string

## Results
- PASS/FAIL: Pendiente
