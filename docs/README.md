# Documentación del Proyecto

## Estructura

```
docs/
├── arquitectura/           # Diseño técnico y modelo de datos
│   └── modelo-datos.md     # Jerarquía geográfica, tablas PostGIS, flujo de merges
│
├── guias/                  # Guías prácticas
│   ├── setup-docker.md     # Levantar el proyecto con Docker Compose
│   └── agregar-rubro.md    # Paso a paso para agregar un nuevo rubro temático
│
├── datos/                  # Catálogo de datos
│   └── diccionario.md      # Columnas, tablas, fuentes y CRS
│
└── decisiones/             # Architecture Decision Records (ADRs)
    └── 20240101-dos-apps-dash.md
```

## Por crear

- `docs/arquitectura/flujo-datos.md` — Pipeline completo de ingesta hasta visualización
- `docs/guias/setup-local.md` — Desarrollo sin Docker (venv + DB local)
- `docs/guias/ingesta-datos.md` — Importar shapefiles a PostGIS
- `docs/datos/fuentes.md` — Catálogo detallado de fuentes con URLs de descarga
- `docs/datos/transformaciones.md` — Reglas de limpieza y cálculos derivados
