# Validation

## Commands
```bash
# App responde
curl -I https://<app-name>.onrender.com/

# Dashboard carga
curl -s https://<app-name>.onrender.com/dashboard/ | grep -c "Coyoacán"

# Wake-up time (después de sleep)
time curl -s https://<app-name>.onrender.com/ > /dev/null
```

## Checklist
- [ ] URL pública accesible
- [ ] Login funcional
- [ ] Mapa de polígonos renderiza
- [ ] Variables de entorno configuradas en Render
- [ ] UptimeRobot configurado (ping cada 14 min)
- [ ] docs/guias/setup-neon-render.md creado
- [ ] CLAUDE.md actualizado
- [ ] Costo mensual: $0

## Results
- PASS/FAIL: Pendiente
