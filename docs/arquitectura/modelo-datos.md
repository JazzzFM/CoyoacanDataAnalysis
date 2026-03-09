# Modelo de Datos

## Jerarquía Geográfica

La unidad fundamental del proyecto es la jerarquía geográfica de Coyoacán:

```
Municipio (1)
└── Colonia (153)
    └── AGEB (167)
        └── Manzana (4,460)
```

Los tres niveles inferiores se almacenan en una sola tabla PostGIS (`poligonos_manzanas_agebs_colonias`) con geometrías separadas por nivel:

```
poligonos_manzanas_agebs_colonias
├── ID_MANZANA + GEOM_MANZANA   (4,403 polígonos)
├── ID_AGEB    + GEOM_AGEB      (polígonos de AGEB)
├── ID_COLONIA + GEOM_COLONIA   (polígonos de colonia)
└── NOMBRE_COLONIA              (nombre legible)
```

## Tablas Temáticas

Los datos temáticos se almacenan en tablas separadas, cada una con su propia granularidad nativa:

| Tabla | Granularidad Nativa | Clave de Join | Geometría Propia |
|---|---|---|---|
| `datos_demograficos_particionada` | AGEB | `ageb` → `ID_AGEB` | `geometry` |
| `datos_edafologicos_particionada` | Manzana | `ID_MANZANA` → `ID_MANZANA` | `GEOM_MANZANA` |

## Flujo de Merge en el Dashboard

El merge entre polígonos y datos temáticos ocurre en `CallbackRegister` y varía según el rubro y la granularidad seleccionada:

### Demográficos

Siempre se une por `ID_AGEB`, sin importar la granularidad de visualización:

```
poligonos_[granularidad]  LEFT JOIN  datos_demograficos
     ID_AGEB           ←→        ageb
```

Esto significa que al visualizar a nivel manzana, muchas manzanas dentro del mismo AGEB tendrán los mismos valores demográficos (el dato es del AGEB, no de la manzana individual).

### Edafológicos

Se une por `ID_MANZANA` (y opcionalmente `GEOM_MANZANA`):

```
# Granularidad manzana o colonia:
poligonos  LEFT JOIN  datos_edafologicos
  ID_MANZANA + GEOM_MANZANA  ←→  ID_MANZANA + GEOM_MANZANA

# Granularidad AGEB:
poligonos  LEFT JOIN  datos_edafologicos
  ID_MANZANA  ←→  ID_MANZANA
```

## Agregación por Granularidad

Después del merge, `DataService.obtener_datos_filtrados()` agrupa los datos según la granularidad seleccionada por el usuario:

### Nivel Manzana (sin agregación)
```python
gdf = gdf[metricas + tooltip_cols + ["ID_MANZANA", "GEOM_MANZANA"]]
gdf = gdf.set_geometry("GEOM_MANZANA")
```

### Nivel AGEB
```python
gdf = gdf.groupby(metricas + tooltip_cols + ["ID_AGEB", "GEOM_AGEB"]).first()
gdf = gdf.set_geometry("GEOM_AGEB")
```

### Nivel Colonia (demográficos)
```python
gdf = gdf.groupby(metricas + tooltip_cols + ["ID_COLONIA", "GEOM_COLONIA"]).first()
gdf = gdf.set_geometry("GEOM_COLONIA")
```

### Nivel Colonia (edafológicos) - Lógica especial
En lugar de un simple groupby, se busca el uso de suelo predominante por colonia:

```python
# Contar combinaciones de atributos por colonia
gdf_ = gdf.groupby(['ID_COLONIA', 'USO_SUELO', 'SUPERFICIE', ...]).size()
# Quedarse con la combinación más frecuente
gdf_ = gdf_.sort_values('counts', ascending=False).drop_duplicates('ID_COLONIA')
# Unir de vuelta con geometría de colonia
gdf = gdf[['ID_COLONIA', 'GEOM_COLONIA']].merge(gdf_, on='ID_COLONIA')
```

## Tooltip Columns por Rubro

Cada rubro define qué columnas se muestran en el hover del mapa (definido en `DashboardFilters.__post_init__`):

| Rubro | Columnas de Tooltip |
|---|---|
| Demográficos | `ID_AGEB`, `NOMBRE_COLONIA`, `alc`, `amb_loc`, `area_km2` |
| Edafológicos | `ID_AGEB`, `NOMBRE_COLONIA`, `USO_SUELO`, `DNSDD_D`, `NIVELES`, `ALTURA` |

## Diagrama de Relaciones

```
┌─────────────────────────────────────┐
│ poligonos_manzanas_agebs_colonias   │
│                                     │
│  ID_MANZANA ─────────────────────┐  │
│  ID_AGEB ──────────────────┐     │  │
│  ID_COLONIA                │     │  │
│  NOMBRE_COLONIA            │     │  │
│  GEOM_MANZANA              │     │  │
│  GEOM_AGEB                 │     │  │
│  GEOM_COLONIA              │     │  │
└────────────────────────────┼─────┼──┘
                             │     │
            ┌────────────────┘     └──────────────────┐
            │ JOIN: ageb ←→ ID_AGEB                   │ JOIN: ID_MANZANA ←→ ID_MANZANA
            ▼                                         ▼
┌───────────────────────────┐          ┌──────────────────────────────┐
│ datos_demograficos_       │          │ datos_edafologicos_          │
│ particionada              │          │ particionada                 │
│                           │          │                              │
│  ageb (CVEGEO 13 dígitos) │          │  ID_MANZANA                  │
│  pob_total, pob_hombres   │          │  USO_SUELO, SUPERFICIE       │
│  pob_mujeres              │          │  DNSDD_D, NIVELES, ALTURA    │
│  area_km2, densidad_*     │          │  GEOM_MANZANA                │
│  t_* (tasas porcentuales) │          │  anio, territorio            │
│  anio, territorio         │          │                              │
│  geometry                 │          │                              │
└───────────────────────────┘          └──────────────────────────────┘
```
