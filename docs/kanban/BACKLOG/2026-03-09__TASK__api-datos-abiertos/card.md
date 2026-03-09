---
id: "TASK-2026-03-09__api-datos-abiertos"
title: "API REST de datos abiertos para investigadores y periodistas"
status: "BACKLOG"
phase: "Plan"
scope_in:
  - "Endpoints REST para consultar datos por colonia/AGEB/manzana"
  - "Formato GeoJSON para integración con otros sistemas GIS"
  - "Documentación OpenAPI/Swagger"
  - "Rate limiting para free tier"
  - "Endpoint de descarga bulk (CSV, GeoJSON)"
scope_out:
  - "Autenticación con API keys (v1 es pública)"
  - "Endpoints de escritura"
artifacts:
  card: card.md
plan_phase: 4
---

# Summary
- Objective: Multiplicar el impacto del proyecto permitiendo que otros investigadores, periodistas y desarrolladores consuman los datos programáticamente.
- Constraints: Debe funcionar en Render free tier (512 MB RAM). Flask puede servir como API REST nativa.

# Endpoints propuestos
```
GET /api/v1/colonias                          # Lista de colonias con geometría
GET /api/v1/colonias/{nombre}                 # Detalle de una colonia
GET /api/v1/colonias/{nombre}/demograficos    # Datos demográficos
GET /api/v1/colonias/{nombre}/uso-suelo       # Uso de suelo
GET /api/v1/agebs                             # Lista de AGEBs
GET /api/v1/agebs/{id}/demograficos           # Datos por AGEB
GET /api/v1/servicios?categoria=salud&radio=500  # Servicios en radio
GET /api/v1/vulnerabilidad                    # Índice de vulnerabilidad
GET /api/v1/export/geojson?tabla=demograficos # Descarga bulk
```

# Usuarios objetivo
- **Investigador:** Descarga datos para análisis propio (R, Python, QGIS)
- **Periodista:** Consulta datos específicos para reportajes con evidencia
- **Desarrollador:** Integra datos en sus propias aplicaciones

# Dependencias
- **Requiere:** REFACTOR__unificar-apps-dash (endpoints viven en Flask)
- **Requiere:** Al menos 3 rubros con datos
- **Bloquea:** Nada

# Updates
- 2026-03-09 - Created.
