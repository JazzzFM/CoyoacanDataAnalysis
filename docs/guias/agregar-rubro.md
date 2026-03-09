# Cómo Agregar un Nuevo Rubro Temático

Guía paso a paso para agregar un nuevo rubro (ej: electorales, servicios, ambientales) al dashboard standalone (`dashboard/`).

---

## Prerequisitos

1. Los datos del nuevo rubro deben estar cargados en PostGIS como tabla con columna de geometría
2. La tabla debe tener una columna que permita hacer join con `poligonos_manzanas_agebs_colonias` (típicamente `ID_MANZANA`, `ID_AGEB`, o un código AGEB)

---

## Paso 1: Registrar la tabla en `TableController`

**Archivo:** `dashboard/domain/domain_models.py`

Agregar la configuración de la nueva tabla en `TableController.__post_init__`:

```python
@dataclass
class TableController:
    # ...campos existentes...
    electorales: object = field(init=False)  # Agregar si no existe

    def __post_init__(self):
        # ...tablas existentes...

        self.electorales = {
            "table_name": "datos_electorales_particionada",  # Nombre en PostGIS
            "geom_column": "geometry"  # Columna de geometría en esa tabla
        }
```

## Paso 2: Definir las columnas de tooltip

**Archivo:** `dashboard/domain/domain_models.py`

En `DashboardFilters.__post_init__`, agregar el bloque para el nuevo rubro:

```python
def __post_init__(self):
    if self.type_data == "demograficos":
        self.tooltip_cols = [...]
    elif self.type_data == "edafologicos":
        self.tooltip_cols = [...]
    elif self.type_data == "electorales":  # NUEVO
        self.tooltip_cols = [
            "ID_AGEB",
            "NOMBRE_COLONIA",
            "partido",           # Columnas específicas del rubro
            "votos_totales",
        ]
```

Estas columnas aparecen en el hover del mapa coroplético.

## Paso 3: Agregar la lógica de merge

**Archivo:** `dashboard/presentation/callback_register.py`

En `_register_map_callback`, dentro de la función `actualizar_mapa`, agregar la lógica de merge para cada granularidad. Seguir el patrón existente:

```python
# Dentro de actualizar_mapa():
if gran == 'manzana':
    # ...casos existentes...
    elif dataset_key == 'electorales':  # NUEVO
        self.gdf_poligonos_data = merge(
            self.poligonos_manzana,
            self.data,
            left_on=['ID_AGEB'],      # Ajustar según clave de join
            right_on=['ageb'],
            how='left')

elif gran == 'colonia':
    # ...mismo patrón para colonia...

elif gran == 'ageb':
    # ...mismo patrón para ageb...
```

La clave de join depende de la granularidad nativa de los datos:
- Si los datos son a nivel AGEB: join por `ID_AGEB` ←→ `ageb`
- Si los datos son a nivel Manzana: join por `ID_MANZANA` ←→ `ID_MANZANA`

## Paso 4: Agregar la navegación de página

**Archivo:** `dashboard/presentation/callback_register.py`

En `_register_page_callback`, dentro de `render_page_content`, agregar el caso para la ruta:

```python
elif pathname == "/electorales":
    self.data = self.data_service\
        .initialize_dataset(self.table_controller.electorales)
    anios = self.data_service\
        .obtener_anios_disponibles(self.data)
    page = self.page_builder\
        .create_electorales_page(anios)
    return page
```

## Paso 5: Crear la página en el layout

**Archivo:** `dashboard/presentation/layout_builder.py`

Agregar el método para la nueva página (si no existe ya):

```python
def create_electorales_page(self, anios: List[int]) -> html.Div:
    return html.Div([
        html.H3("Rubro: Tablero Electoral"),
        self.create_filter_row(anios),
        html.Div(id="mapa-plotly")
    ])
```

La barra lateral (`create_layout`) ya incluye el NavLink para todos los rubros planificados. Si el rubro es completamente nuevo, agregar el enlace ahí también.

## Paso 6 (Si aplica): Lógica de agregación especial

**Archivo:** `dashboard/services/data_service.py`

Si el nuevo rubro requiere lógica de agregación diferente al hacer groupby por granularidad (como los edafológicos al agrupar por colonia), modificar `obtener_datos_filtrados`:

```python
elif filters.granularidad == "colonia":
    if filters.type_data == "demograficos":
        # ...lógica existente...
    elif filters.type_data == "edafologicos":
        # ...lógica existente...
    elif filters.type_data == "electorales":  # NUEVO
        # Lógica de agregación específica
        agrupa = columnas_fijas + metricas + ["ID_COLONIA", "GEOM_COLONIA"]
        gdf = gdf.groupby(list(set(agrupa))).sum().reset_index()
        gdf = gdf.set_geometry("GEOM_COLONIA")
```

## Paso 7: Verificar el parseo de ruta

**Archivo:** `dashboard/presentation/callback_register.py`

Confirmar que `_parse_dataset_key` ya tiene el caso para la nueva ruta:

```python
def _parse_dataset_key(self, pathname: str) -> str:
    # ...ya debería existir si el rubro estaba planificado...
    elif pathname == "/electorales":
        return "electorales"
```

---

## Resumen de archivos a modificar

| # | Archivo | Qué modificar |
|---|---|---|
| 1 | `domain/domain_models.py` | `TableController.__post_init__` + `DashboardFilters.__post_init__` |
| 2 | `presentation/callback_register.py` | `render_page_content` + `actualizar_mapa` (merges) + `_parse_dataset_key` |
| 3 | `presentation/layout_builder.py` | Método `create_<rubro>_page` (si no existe) |
| 4 | `services/data_service.py` | `obtener_datos_filtrados` (solo si hay lógica de agregación especial) |

---

## Checklist

- [ ] Tabla cargada en PostGIS con geometría y columna de año (`anio`)
- [ ] `TableController` tiene el diccionario `{table_name, geom_column}` del nuevo rubro
- [ ] `DashboardFilters` define `tooltip_cols` para el nuevo `type_data`
- [ ] `CallbackRegister` tiene lógica de merge para las 3 granularidades
- [ ] `CallbackRegister.render_page_content` maneja la ruta nueva
- [ ] `LayoutBuilder` tiene método `create_<rubro>_page`
- [ ] `_parse_dataset_key` reconoce el pathname
- [ ] NavLink en `create_layout` (sidebar) apunta a la ruta correcta
- [ ] Probado con las 3 granularidades: manzana, ageb, colonia
