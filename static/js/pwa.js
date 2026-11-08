/*
 * HoraSalud · app instalable y avisos push (B-14).
 *
 * En cualquier página registra el service worker. Si la página tiene un panel
 * [data-panel-app], muestra según corresponda:
 *  - "Instalar HoraSalud" (Android/Chrome) o cómo agregarla en iPhone;
 *  - "Activar avisos": pide permiso y guarda el dispositivo en el servidor;
 *  - "Probar aviso": manda un aviso de prueba al propio teléfono.
 */
(function () {
  'use strict';
  if (!('serviceWorker' in navigator)) return;

  // Si el navegador no permite service workers (o falla), la app sigue funcionando: solo no habrá avisos.
  var registro = navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(function () { return null; });
  var eventoInstalar = null;
  var panel = document.querySelector('[data-panel-app]');

  function $(selector) { return panel ? panel.querySelector(selector) : null; }
  function mostrar(selector, visible) {
    if (!panel) return;
    panel.querySelectorAll(selector).forEach(function (el) { el.hidden = !visible; });
  }
  function texto(selector, valor) { var el = $(selector); if (el) el.textContent = valor; }

  function csrf() {
    var meta = document.querySelector('meta[name=csrf-token]');
    return meta ? meta.content : '';
  }

  function enviar(url, datos) {
    return fetch(url, {
      method: 'POST', credentials: 'same-origin',
      headers: { 'X-CSRFToken': csrf(), 'Content-Type': 'application/json' },
      body: JSON.stringify(datos || {}),
    }).then(function (r) { return r.json().catch(function () { return { ok: r.ok }; }); });
  }

  // Clave pública VAPID en base64url -> bytes (lo que pide el navegador)
  function claveEnBytes(base64) {
    var relleno = '='.repeat((4 - (base64.length % 4)) % 4);
    var crudo = atob((base64 + relleno).replace(/-/g, '+').replace(/_/g, '/'));
    var bytes = new Uint8Array(crudo.length);
    for (var i = 0; i < crudo.length; i++) bytes[i] = crudo.charCodeAt(i);
    return bytes;
  }

  var instalada = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
  var esIphone = /iphone|ipad|ipod/i.test(navigator.userAgent);
  var permiteAvisos = 'PushManager' in window && 'Notification' in window;

  // ---------- Instalar ----------
  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    eventoInstalar = e;
    mostrar('[data-instalar]', true);
  });
  window.addEventListener('appinstalled', function () {
    mostrar('[data-instalar]', false);
    mostrar('[data-instalada]', true);
  });

  if (!panel) return;
  mostrar('[data-instalada]', instalada);
  mostrar('[data-iphone]', esIphone && !instalada);

  var botonInstalar = $('[data-instalar]');
  if (botonInstalar) botonInstalar.addEventListener('click', function () {
    if (!eventoInstalar) return;
    eventoInstalar.prompt();
    eventoInstalar.userChoice.then(function () { eventoInstalar = null; mostrar('[data-instalar]', false); });
  });

  // ---------- Avisos ----------
  var clavePublica = panel.getAttribute('data-clave') || '';

  function estadoAvisos(estado, detalle) {
    mostrar('[data-avisos-activar]', estado === 'apagados');
    mostrar('[data-avisos-activos]', estado === 'activos');
    mostrar('[data-avisos-bloqueados]', estado === 'bloqueados');
    mostrar('[data-avisos-no-disponible]', estado === 'no-disponible');
    if (detalle) texto('[data-avisos-mensaje]', detalle);
  }

  if (!permiteAvisos || !clavePublica) {
    estadoAvisos('no-disponible');
    return;
  }

  function guardar(suscripcion) {
    return enviar('/avisos/suscribir/', suscripcion.toJSON());
  }

  if (Notification.permission === 'denied') estadoAvisos('bloqueados');
  registro.then(function (reg) {
    if (!reg) return estadoAvisos(Notification.permission === 'denied' ? 'bloqueados' : 'no-disponible');
    return reg.pushManager.getSubscription().then(function (actual) {
      if (Notification.permission === 'denied') return estadoAvisos('bloqueados');
      if (actual) { guardar(actual); return estadoAvisos('activos'); }
      estadoAvisos('apagados');
    });
  }).catch(function () { estadoAvisos('no-disponible'); });

  var botonActivar = $('[data-avisos-activar]');
  if (botonActivar) botonActivar.addEventListener('click', function () {
    botonActivar.disabled = true;
    Notification.requestPermission().then(function (permiso) {
      if (permiso !== 'granted') { estadoAvisos('bloqueados'); return null; }
      return registro.then(function (reg) {
        if (!reg) throw new Error('sin service worker');
        return reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: claveEnBytes(clavePublica) });
      }).then(guardar).then(function (r) {
        estadoAvisos(r && r.ok ? 'activos' : 'apagados', r && r.ok ? '' : (r.error || 'No se pudo activar.'));
      });
    }).catch(function () {
      estadoAvisos('apagados', 'No se pudo activar los avisos. Intenta de nuevo.');
    }).then(function () { botonActivar.disabled = false; });
  });

  var botonProbar = $('[data-avisos-probar]');
  if (botonProbar) botonProbar.addEventListener('click', function () {
    botonProbar.disabled = true;
    texto('[data-avisos-mensaje]', 'Enviando aviso de prueba…');
    enviar('/avisos/prueba/').then(function (r) {
      texto('[data-avisos-mensaje]', r.ok ? 'Aviso enviado: debería sonar en unos segundos.'
                                          : (r.error || 'No llegó el aviso. Revisa la conexión a internet.'));
    }).then(function () { botonProbar.disabled = false; });
  });
})();
