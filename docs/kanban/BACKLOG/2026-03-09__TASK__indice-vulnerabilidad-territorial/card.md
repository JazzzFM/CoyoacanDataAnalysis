---
id: "TASK-2026-03-09__indice-vulnerabilidad-territorial"
title: "Crear índice compuesto de vulnerabilidad territorial"
status: "BACKLOG"
phase: "Research"
scope_in:
  - "Definir variables del índice (demografía + uso suelo + servicios)"
  - "Normalizar variables (min-max o z-score)"
  - "Calcular índice ponderado por AGEB y colonia"
  - "Visualizar en mapa coroplético con semáforo (rojo/amarillo/verde)"
  - "Almacenar en tabla o vista materializada en PostGIS"
  - "Panel de desglose: al hacer click ver qué componentes contribuyen más"
scope_out:
  - "Validación estadística formal (peer review)"
  - "Índice oficial (solo es propuesta analítica)"
artifacts:
  card: card.md
plan_phase: 2
---

# Summary
- Objective: Crear un indicador compuesto que identifique las zonas más vulnerables de Coyoacán combinando múltiples dimensiones. Esto convierte datos crudos en inteligencia territorial accionable.
- Constraints: Depende de cuántos rubros de datos estén cargados. Con solo demografía + uso de suelo ya se puede hacer una versión inicial.

# Componentes del índice (propuesta)

| Dimensión | Variables | Peso sugerido | Fuente |
|-----------|-----------|---------------|--------|
| Demográfica | Densidad, dependencia infantil, % pob indígena | 30% | INEGI 2020 |
| Uso de suelo | % habitacional, densidad construcción, niveles | 20% | SEDUVI 2017 |
| Accesibilidad | Distancia a salud, educación, comercio | 25% | DENUE 2024 |
| Ambiental | Proximidad a áreas verdes, calidad aire | 15% | Por definir |
| Económica | Diversidad comercial, personal ocupado | 10% | DENUE 2024 |

# Metodología
1. Normalizar cada variable a escala 0-1 (min-max por alcaldía)
2. Invertir variables positivas (más población indígena = más vulnerable)
3. Promediar ponderado por dimensión
4. Clasificar en quintiles: Muy baja / Baja / Media / Alta / Muy alta
5. Visualizar con paleta divergente (verde → rojo)

# Usuarios objetivo
- **Investigador:** Valida metodología, ajusta pesos, publica hallazgos
- **Funcionario:** Identifica zonas prioritarias para intervención
- **Ciudadano:** Entiende nivel de vulnerabilidad de su colonia

# Dependencias
- **Requiere:** Datos demográficos cargados (mínimo)
- **Ideal:** También DENUE y ambientales
- **Bloquea:** TASK__recomendador-politicas

# Updates
- 2026-03-09 - Created.
