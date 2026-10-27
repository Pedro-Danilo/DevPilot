# Technology Options
## Drivers y restricciones
RF-002 exige coherencia de ventas e inventario, con una sola operadora local.
## Opción T1 — Python local
- **Stack:** Python, SQLite y UI ligera, monolito modular.
- **Costo y licencias:** licencias abiertas, costo de soporte local limitado.
- **Soporte:** comunidad estable y equipo familiarizado con Python.
- **Seguridad:** separación de roles y aprobación de cambios sensibles.
- **Operación:** un proceso local, copia y restauración verificables.
- **Riesgos:** vigilar crecimiento real antes de migrar persistencia.
## Opción T2 — Python servidor local
- **Stack:** Python, PostgreSQL y UI web separada.
- **Costo y licencias:** abierto, mayor coste operativo del servidor.
- **Soporte:** comunidad estable y mantenimiento de servidor adicional.
- **Seguridad:** controles equivalentes y gestión separada de acceso.
- **Operación:** dos procesos, soporte y respaldo más complejos.
- **Riesgos:** mayor carga para una persona sin ventaja MVP inmediata.
## Recomendación razonada
Preferir T1 por complejidad y mantenimiento menores en el MVP actual; T2
se evaluaría al crecer concurrencia verificada y demanda centralizada.
