---
id: "DATA-2026-03-09__ingesta-datos-abiertos-cdmx"
title: "Ingesta de datos abiertos CDMX para enriquecer análisis territorial"
status: "BACKLOG"
phase: "Research"
scope_in:
  - "Descargar datasets SHP de datos.cdmx.gob.mx"
  - "Filtrar/recortar a Coyoacán"
  - "Crear scripts ETL para cada dataset"
  - "Cargar a Neon PostGIS"
  - "Integrar al dashboard (nuevos rubros o capas)"
scope_out:
  - "Análisis estadístico avanzado (correlaciones, modelos)"
  - "Datos de portales que no sean gobierno CDMX"
  - "Datos que requieran convenio o acceso restringido"
artifacts:
  card: card.md
  research: research.md
plan_phase: 2
---

# Summary
- Objective: Enriquecer la plataforma de análisis territorial de Coyoacán con datasets geoespaciales abiertos de la CDMX, cubriendo transporte, seguridad, medio ambiente, economía y vivienda.
- Constraints: Todos los datasets son públicos bajo licencia CC-BY 4.0. Formato SHP. Portal principal: datos.cdmx.gob.mx (247 datasets SHP disponibles).

# Portal principal
- **datos.cdmx.gob.mx** -- 247 datasets SHP, 119 GeoJSON (fuente primaria)
- **datamx.io** -- Mayormente Jalisco, poco útil para Coyoacán
- **datos.gob.mx** -- Datasets nacionales (CONAPO, CONEVAL) recortables a CDMX

# Prioridad 1: Gentrificación (alineado con Phase 4 del roadmap)

## 1.1 Valor unitario del suelo habitacional
- **URL:** datos.cdmx.gob.mx/dataset/valores-unitarios-del-suelo-habitacional-habitacional-comercial-en-pesos-valor-promedio
- **Descripción:** Precios de suelo por zona (habitacional y comercial)
- **Valor:** Indicador clave de gentrificación -- mapear precios por colonia/zona
- **Formato:** SHP

## 1.2 Incremento de población 2000-2010 + valor vivienda 2006-2019
- **URL:** datos.cdmx.gob.mx/dataset/incremento-absoluto-de-poblacion-2000-2010-y-valor-de-la-vivienda-2006-2019
- **Descripción:** Cambio poblacional + cambio en valor de vivienda
- **Valor:** Rastrea directamente la dinámica de gentrificación temporal
- **Formato:** SHP

## 1.3 Viviendas desocupadas por colonia
- **URL:** datos.cdmx.gob.mx/dataset/porcentaje-de-viviendas-desocupadas-por-colonia
- **Descripción:** Porcentaje de viviendas vacías por colonia
- **Valor:** Tasa de vacancia como señal de especulación inmobiliaria
- **Formato:** SHP

## 1.4 UE de servicios al turismo por colonia
- **URL:** datos.cdmx.gob.mx/dataset/ue-servicios-turismo
- **Descripción:** Negocios orientados a turismo por colonia
- **Valor:** Presión turística -- indicador complementario de gentrificación
- **Formato:** SHP

## 1.5 Densidad habitacional por colonia
- **URL:** datos.cdmx.gob.mx/dataset/densidad-habitacional-por-colonia-viv-ha
- **Descripción:** Densidad de viviendas por hectárea por colonia
- **Valor:** Patrones de densificación urbana
- **Formato:** SHP

## 1.6 Índice de calidad y espacios de la vivienda
- **URL:** datos.cdmx.gob.mx/dataset/indice-calidad-espacios-de-la-vivienda
- **Descripción:** Índice de calidad habitacional (EVALUA 2015)
- **Valor:** Calidad de vivienda por zona
- **Formato:** SHP

# Prioridad 2: Transporte y movilidad

## 2.1 Metro -- líneas y estaciones
- **URL:** datos.cdmx.gob.mx/dataset/lineas-y-estaciones-del-metro
- **Descripción:** Líneas y estaciones del STC Metro
- **Valor:** Coyoacán tiene estaciones de Líneas 2 y 3
- **Formato:** SHP, GeoJSON, KMZ

## 2.2 Tren Ligero -- líneas y estaciones
- **URL:** datos.cdmx.gob.mx/dataset/geolocalizacion-de-lineas-y-estaciones-paradas-del-servicio-de-transportes-electricos
- **Descripción:** Tren Ligero (Taxqueña-Xochimilco) pasa por Coyoacán
- **Formato:** SHP

## 2.3 Metrobús -- líneas y estaciones
- **URL:** datos.cdmx.gob.mx/dataset/geolocalizacion-metrobus
- **Descripción:** Sistema BRT de la CDMX
- **Formato:** SHP, GeoJSON, KMZ

## 2.4 Áreas de influencia Metro (800m) y Tren Ligero (400m)
- **URL:** datos.cdmx.gob.mx/dataset/area-de-influencia-del-sistema-de-transporte-colectivo-metro-800-mts
- **URL:** datos.cdmx.gob.mx/dataset/area-de-influencia-del-tren-ligero-400-mts
- **Descripción:** Polígonos de cobertura peatonal pre-calculados
- **Valor:** Ahorra trabajo GIS; mapa directo de accesibilidad al transporte
- **Formato:** SHP

## 2.5 Infraestructura vial ciclista
- **URL:** datos.cdmx.gob.mx/dataset/infraestructura-vial-ciclista
- **Descripción:** 651 segmentos de ciclovías (actualizado marzo 2025)
- **Formato:** SHP

## 2.6 Sistemas de transporte por manzana
- **URL:** datos.cdmx.gob.mx/dataset/numero-de-sistemas-de-transporte-disponibles-por-manzana
- **Descripción:** Conteo de sistemas de transporte accesibles por manzana
- **Valor:** Índice multimodal a nivel manzana (granularidad máxima)
- **Formato:** SHP

## 2.7 Ecobici -- cicloestaciones y área de influencia (500m)
- **URL:** datos.cdmx.gob.mx/dataset/cicloestaciones-ecobici-nuevo-sistema
- **URL:** datos.cdmx.gob.mx/dataset/area-de-influencia-de-ecobici-500-mts
- **Formato:** SHP

## 2.8 Accidentes a peatones
- **URL:** datos.cdmx.gob.mx/dataset/puntos-de-accidentes-a-peatones
- **Descripción:** Puntos de accidentes peatonales geolocalizados
- **Valor:** Hotspots de seguridad vial
- **Formato:** SHP

# Prioridad 3: Seguridad y riesgo

## 3.1 Marginalidad y violencia urbana por colonia
- **URL:** datos.cdmx.gob.mx/dataset/grado-de-marginalidad-y-violencia-urbana-por-colonia-en-la-ciudad-de-mexico
- **Descripción:** Índice combinado de marginalidad + violencia por colonia
- **Valor:** Índice listo para mapear directamente
- **Formato:** SHP, GeoJSON

## 3.2 Zonificación sísmica por colonia
- **URL:** datos.cdmx.gob.mx/dataset/zonificacion-sismica-por-colonia
- **Descripción:** Clasificación de riesgo sísmico por colonia
- **Valor:** Especialmente relevante post-2017
- **Formato:** SHP

## 3.3 Atlas de riesgo -- Inundaciones
- **URL:** datos.cdmx.gob.mx/dataset/atlas-de-riesgo-inundaciones
- **Descripción:** Riesgo de inundación a nivel AGEB
- **Formato:** SHP

## 3.4 Convergencia de múltiples riesgos
- **URL:** datos.cdmx.gob.mx/dataset/convergencia-de-multiples-riesgos-en-la-ciudad-de-mexico
- **Descripción:** Zonas de riesgo múltiple (sismo, inundación, calor, deslizamiento)
- **Formato:** SHP

## 3.5 Carpetas de investigación FGJ
- **URL:** datos.cdmx.gob.mx/dataset/carpetas-de-investigacion-fgj-de-la-ciudad-de-mexico
- **Descripción:** Casos de investigación criminal geocodificados
- **Valor:** Mapeo de criminalidad por tipo y zona
- **Formato:** CSV (geocodificado)

# Prioridad 4: Medio ambiente

## 4.1 Inventario de Áreas Verdes
- **URL:** datos.cdmx.gob.mx/dataset/inventario-de-areas-verdes-en-la-ciudad-de-mexico
- **Descripción:** Inventario completo de espacios verdes
- **Formato:** SHP

## 4.2 m2 de espacio público por habitante por colonia
- **URL:** datos.cdmx.gob.mx/dataset/metros-cuadrados-de-espacio-publico-por-habitantes
- **Descripción:** Métrica comparativa vs estándar OMS (9 m2/persona)
- **Formato:** SHP

## 4.3 Rezago de espacio público por colonia
- **URL:** datos.cdmx.gob.mx/dataset/rezago-de-espacio-publico-por-colonia
- **Descripción:** Análisis multicriterio de déficit de espacio público
- **Formato:** SHP

## 4.4 Temperatura superficial nocturna
- **URL:** datos.cdmx.gob.mx/dataset/temperatura-nocturna-cdmx
- **Descripción:** Temperatura de superficie nocturna (isla de calor)
- **Formato:** SHP

## 4.5 Consumo habitacional de agua por colonia
- **URL:** datos.cdmx.gob.mx/dataset/consumo-habitacional-promedio-bimestral-de-agua-por-colonia-m3
- **Descripción:** Consumo promedio bimestral de agua por colonia
- **Formato:** SHP

## 4.6 Deforestación en suelo urbano
- **URL:** datos.cdmx.gob.mx/dataset/ca-8-deforestacion-en-suelo-urbano
- **Descripción:** Pérdida de áreas verdes urbanas 1996-2016
- **Formato:** SHP

# Prioridad 5: Infraestructura y equipamiento

## 5.1 Equipamiento básico de salud
- **URL:** datos.cdmx.gob.mx/dataset/equipamiento-basico-de-salud
- **Descripción:** Centros de salud por colonia
- **Formato:** SHP

## 5.2 Escuelas de educación básica por colonia
- **URL:** datos.cdmx.gob.mx/dataset/escuelas-de-educacion-basica-por-colonia-en-la-ciudad-de-mexico
- **Formato:** SHP

## 5.3 Tianguis de la CDMX
- **URL:** datos.cdmx.gob.mx/dataset/tianguis-de-la-ciudad-de-mexico
- **Descripción:** Mercados informales/tradicionales
- **Formato:** SHP

## 5.4 Zonas de Monumentos Históricos (INAH)
- **URL:** datos.cdmx.gob.mx/dataset/zonas-monumentos-historicos
- **Descripción:** Perímetros de zonas protegidas por INAH
- **Valor:** Centro Histórico de Coyoacán
- **Formato:** SHP, CSV

## 5.5 Infraestructura peatonal por colonia
- **URL:** datos.cdmx.gob.mx/dataset/nivel-de-presencia-de-infraestructura-peatonal-por-colonia
- **Descripción:** Índice de caminabilidad por colonia
- **Formato:** SHP

## 5.6 Concentración de equipamientos por km2
- **URL:** datos.cdmx.gob.mx/dataset/concentracion-de-equipamientos-por-km2-de-la-ciudad-de-mexico
- **Descripción:** Densidad de equipamiento médico, escuelas, espacios públicos
- **Formato:** SHP

# Prioridad 6: Economía y vivienda (complementarios)

## 6.1 Densidad de UE comerciales por colonia
- **URL:** datos.cdmx.gob.mx/dataset/densidad-de-unidades-economicas-comeciales-por-colonia
- **Formato:** SHP

## 6.2 Zonas por nivel de ingresos de hogares
- **URL:** datos.cdmx.gob.mx/dataset/ingresos-trimestrales-2018
- **Descripción:** Estratificación de ingresos (ENIGH)
- **Formato:** SHP

## 6.3 Principales corredores económicos
- **URL:** datos.cdmx.gob.mx/dataset/principales-corredores-economicos-en-la-ciudad-de-mexico
- **Descripción:** Insurgentes, Reforma y otros corredores económicos
- **Formato:** SHP

## 6.4 Tasa de crecimiento poblacional 2010-2020
- **URL:** datos.cdmx.gob.mx/dataset/tasa-de-crecimiento-medio-anual-2010-2020
- **Formato:** SHP

## 6.5 Internet en viviendas (Censo 2020)
- **URL:** datos.cdmx.gob.mx/dataset/viviendas-con-acceso-a-internet-censo-2020
- **Descripción:** Acceso a internet por AGEB
- **Valor:** Brecha digital
- **Formato:** SHP

# Plan de ejecución sugerido

## Fase A: Gentrificación (Prioridad 1) -- 6 datasets
Alineado con Phase 4 del roadmap. Crear scripts ETL, cargar a PostGIS, crear nuevo rubro en dashboard.

## Fase B: Transporte (Prioridad 2) -- 8 datasets
Crear capa de transporte superpuesta al mapa base. Análisis de accesibilidad multimodal.

## Fase C: Seguridad/Riesgo (Prioridad 3) -- 5 datasets
Nuevo rubro "Seguridad y Riesgo" con índices por colonia.

## Fase D: Medio ambiente (Prioridad 4) -- 6 datasets
Enriquecer rubro "Ambientales" existente.

## Fase E: Infraestructura (Prioridad 5) -- 6 datasets
Capas de equipamiento urbano.

## Fase F: Economía (Prioridad 6) -- 5 datasets
Complementar rubro de servicios con datos económicos por colonia.

# Dependencias
- **Requiere:** Nada (datos públicos)
- **Bloquea:** TASK__deteccion-gentrificacion, TASK__analisis-accesibilidad, TASK__capas-superpuestas, TASK__indice-vulnerabilidad-territorial

# Updates
- 2026-03-09 - Created. Investigación completa de 96+ datasets en datos.cdmx.gob.mx, datamx.io y datos.gob.mx.
