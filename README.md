# PS5 Radar — versión con integración de fuentes web

## Qué hace esta versión
- Interfaz PWA móvil.
- Backend Python/Flask que consulta páginas públicas de:
  - Vandal: calendario de lanzamientos PS5.
  - Vandal: análisis recientes de PS5.
  - PlayStation Store España: página pública de ofertas.
- Caché de 30 minutos para no consultar continuamente las fuentes.
- Actualización al abrir y botón “Actualizar ahora”.
- La lista y los precios objetivo se guardan localmente en el navegador.

## Importante: no es una API oficial
Las integraciones extraen información visible de páginas públicas. El HTML puede cambiar, bloquear solicitudes o mostrar resultados incompletos; por eso hay que verificar siempre los detalles en la fuente original. Esta versión no puede garantizar todos los lanzamientos o todos los análisis publicados por todos los medios españoles. Las notas de análisis pueden no estar disponibles en el listado y no se inventan.

## Instalarla en Android
Para que el navegador permita instalarla como app, debe publicarse con HTTPS:
1. Crea una cuenta en Render (o un hosting Python equivalente).
2. Sube estos archivos a un repositorio GitHub.
3. En Render, crea un servicio web desde ese repositorio. El archivo `render.yaml` contiene la configuración sugerida.
4. Render instalará `requirements.txt` y ejecutará `python server.py`.
5. Abre la URL HTTPS que te dé Render desde Chrome en Android.
6. Menú ⋮ → “Instalar aplicación” o “Añadir a pantalla de inicio”.

## Limitaciones pendientes
- El servidor necesita publicarse para que la app móvil pueda consultar los endpoints `/api/...`.
- No hay aún notificaciones push ni alertas de precio en segundo plano. Los precios objetivo se guardan, pero las alertas automáticas requieren un servicio de tareas programadas y un canal de notificación (correo, Telegram o push).
- La tienda puede cambiar el formato de las tarjetas y hacer que la extracción de ofertas devuelva pocos resultados o ninguno.
- No se usa una API privada de PlayStation Store ni se requiere iniciar sesión en la cuenta de PSN.

## Fuentes conectadas
- https://vandal.elespanol.com/lanzamientos/89/playstation-5
- https://vandal.elespanol.com/analisis/playstation-5
- https://store.playstation.com/es-es/category/c48c22e2-5f2e-40e4-b946-8fdb97a0bc32/1
