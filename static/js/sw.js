/*
 * HoraSalud · service worker (B-14).
 * Programa pequeño que el navegador mantiene aunque la app esté cerrada:
 *  - recibe los avisos push y los muestra con sonido y vibración;
 *  - al tocar el aviso, abre HoraSalud en la pantalla correcta;
 *  - si no hay internet, muestra una página "Sin conexión" en vez de un error.
 * No guarda datos personales ni páginas con datos del paciente.
 */
const CACHE = 'horasalud-v1';
const SIN_CONEXION = '/sin-conexion/';

self.addEventListener('install', (evento) => {
  evento.waitUntil(caches.open(CACHE).then((c) => c.add(SIN_CONEXION)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (evento) => {
  evento.waitUntil(
    caches.keys()
      .then((claves) => Promise.all(claves.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Solo las páginas: si falla la red, se muestra "Sin conexión". Nada se guarda en caché.
self.addEventListener('fetch', (evento) => {
  if (evento.request.mode !== 'navigate') return;
  evento.respondWith(fetch(evento.request).catch(() => caches.match(SIN_CONEXION)));
});

self.addEventListener('push', (evento) => {
  let datos = {};
  try { datos = evento.data ? evento.data.json() : {}; } catch (e) { datos = { texto: evento.data.text() }; }
  evento.waitUntil(self.registration.showNotification(datos.titulo || 'HoraSalud', {
    body: datos.texto || 'Tienes un aviso nuevo en HoraSalud.',
    icon: '/static/images/icono-192.png',
    badge: '/static/images/icono-aviso-96.png',
    vibrate: [300, 150, 300, 150, 600],
    requireInteraction: true, // queda en pantalla hasta que la persona lo toque
    renotify: true,
    tag: datos.etiqueta || 'horasalud',
    lang: 'es-CL',
    data: { url: datos.url || '/mi-inicio/' },
  }));
});

self.addEventListener('notificationclick', (evento) => {
  evento.notification.close();
  const destino = new URL(evento.notification.data.url, self.location.origin).href;
  evento.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((ventanas) => {
      for (const ventana of ventanas) {
        if (new URL(ventana.url).origin === self.location.origin && 'focus' in ventana) {
          return ventana.focus().then((v) => (v && 'navigate' in v ? v.navigate(destino) : v));
        }
      }
      return self.clients.openWindow(destino);
    })
  );
});
