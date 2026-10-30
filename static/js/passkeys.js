/*
 * HoraSalud · Passkeys (WebAuthn) en el navegador (B-06).
 *
 * navigator.credentials.create() / .get() le piden al SISTEMA OPERATIVO la
 * huella, el rostro o el PIN. La pagina nunca recibe el dato biometrico:
 * solo una firma que el servidor verifica con la clave publica.
 */
(function () {
  'use strict';

  // --- base64url <-> bytes ---
  function aBytes(texto) {
    var b64 = texto.replace(/-/g, '+').replace(/_/g, '/');
    while (b64.length % 4) b64 += '=';
    var bin = atob(b64), bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return bytes.buffer;
  }
  function aTexto(buffer) {
    var bytes = new Uint8Array(buffer), bin = '';
    for (var i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
    return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }

  function prepararCreacion(o) {
    o.challenge = aBytes(o.challenge);
    o.user.id = aBytes(o.user.id);
    (o.excludeCredentials || []).forEach(function (c) { c.id = aBytes(c.id); });
    return o;
  }
  function prepararIngreso(o) {
    o.challenge = aBytes(o.challenge);
    (o.allowCredentials || []).forEach(function (c) { c.id = aBytes(c.id); });
    return o;
  }

  function credencialAJson(c) {
    var r = c.response, respuesta = { clientDataJSON: aTexto(r.clientDataJSON) };
    if (r.attestationObject) {
      respuesta.attestationObject = aTexto(r.attestationObject);
      if (r.getTransports) respuesta.transports = r.getTransports();
    } else {
      respuesta.authenticatorData = aTexto(r.authenticatorData);
      respuesta.signature = aTexto(r.signature);
      if (r.userHandle) respuesta.userHandle = aTexto(r.userHandle);
    }
    return {
      id: c.id, rawId: aTexto(c.rawId), type: c.type, response: respuesta,
      authenticatorAttachment: c.authenticatorAttachment || null,
      clientExtensionResults: c.getClientExtensionResults ? c.getClientExtensionResults() : {}
    };
  }

  function csrf() {
    var campo = document.querySelector('[name=csrfmiddlewaretoken]');
    return campo ? campo.value : '';
  }

  function post(url, cuerpo, extra) {
    var cabeceras = { 'X-CSRFToken': csrf(), 'Content-Type': 'application/json' };
    Object.assign(cabeceras, extra || {});
    return fetch(url, { method: 'POST', credentials: 'same-origin', headers: cabeceras, body: cuerpo || '{}' })
      .then(function (r) { return r.json(); })
      .then(function (datos) {
        if (!datos.ok) throw new Error(datos.error || 'Ocurrió un error.');
        return datos;
      });
  }

  function mensajeError(error) {
    if (error && error.name === 'NotAllowedError') return 'Se canceló o se agotó el tiempo. Vuelve a intentarlo.';
    if (error && error.name === 'InvalidStateError') return 'Este dispositivo ya está registrado. Ingresa normalmente.';
    if (error && error.name === 'SecurityError') return 'El navegador bloqueó la huella: abre el sitio con la dirección correcta.';
    return (error && error.message) || 'Ocurrió un error.';
  }

  function nombreDispositivo() {
    var ua = navigator.userAgent;
    var so = /Android/.test(ua) ? 'Android' : /iPhone|iPad/.test(ua) ? 'iPhone/iPad' :
             /Windows/.test(ua) ? 'Windows' : /Mac/.test(ua) ? 'Mac' : 'Otro';
    var nav = /Edg\//.test(ua) ? 'Edge' : /Chrome\//.test(ua) ? 'Chrome' : /Firefox\//.test(ua) ? 'Firefox' :
              /Safari\//.test(ua) ? 'Safari' : 'Navegador';
    return nav + ' en ' + so;
  }

  /** Revisa si este navegador puede usar passkeys aqui. Devuelve un texto de error o null. */
  function problema(rpId) {
    if (!window.PublicKeyCredential || !navigator.credentials) {
      return 'Este navegador no permite huella o rostro. Usa Chrome, Edge o Safari actualizados.';
    }
    if (location.hostname !== rpId) {
      return 'Para usar la huella abre el sitio en ' + location.protocol + '//' + rpId +
             (location.port ? ':' + location.port : '') + location.pathname;
    }
    if (!window.isSecureContext) return 'La huella solo funciona con una conexión segura (HTTPS).';
    return null;
  }

  function registrar(urls) {
    return post(urls.opciones)
      .then(function (d) { return navigator.credentials.create({ publicKey: prepararCreacion(JSON.parse(d.opciones)) }); })
      .then(function (c) { return post(urls.verificar, JSON.stringify(credencialAJson(c)), { 'X-Dispositivo': nombreDispositivo() }); });
  }

  function ingresar(urls) {
    return post(urls.opciones)
      .then(function (d) { return navigator.credentials.get({ publicKey: prepararIngreso(JSON.parse(d.opciones)) }); })
      .then(function (c) { return post(urls.verificar, JSON.stringify(credencialAJson(c))); });
  }

  /** Conecta un boton: muestra estado, llama a la accion y redirige al terminar. */
  function conectar(opciones) {
    var boton = document.getElementById(opciones.boton);
    var estado = document.getElementById(opciones.estado);
    if (!boton) return;
    var aviso = problema(opciones.rpId);
    if (aviso) {
      estado.textContent = aviso;
      estado.className = 'alert alert-warning mt-3';
      boton.disabled = true;
      return;
    }
    boton.addEventListener('click', function () {
      boton.disabled = true;
      estado.className = 'alert alert-info mt-3';
      estado.textContent = 'Sigue las instrucciones de tu dispositivo…';
      opciones.accion(opciones.urls)
        .then(function (d) { estado.className = 'alert alert-success mt-3'; estado.textContent = '¡Listo!'; location.href = d.destino; })
        .catch(function (e) {
          estado.className = 'alert alert-error mt-3';
          estado.textContent = mensajeError(e);
          boton.disabled = false;
        });
    });
  }

  window.HoraSaludPasskey = { registrar: registrar, ingresar: ingresar, conectar: conectar };
})();
