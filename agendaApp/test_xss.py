"""CP-48 (OWASP A03, XSS): el texto que escribe un usuario se muestra escapado, nunca como código.

Se guarda un <script> en campos de texto libre (detalle de una ausencia y nombre de una persona)
y se comprueba que la página lo muestra como texto (&lt;script&gt;) y no lo ejecuta.
"""
from pathlib import Path

from django.conf import settings
from django.urls import reverse

from autenticacionApp.models import Usuario

from .models import AusenciaProfesional
from .test_gestion_agendas import Base, proximo

ATAQUE = '<script>alert("xss")</script>'
ESCAPADO = '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'


class XssTests(Base):
    def test_detalle_de_ausencia_se_muestra_escapado(self):
        admin = Usuario.objects.create(username='adm_xss', rut='32000002-5', tipo_usuario=Usuario.Tipo.ADMINISTRADOR)
        self.client.force_login(admin)
        self.client.post(reverse('agendas_ausencias'), {
            'profesional': self.prof.pk, 'desde': proximo(3), 'hasta': proximo(3),
            'motivo': 'capacitacion', 'detalle': ATAQUE})
        self.assertTrue(AusenciaProfesional.objects.filter(detalle=ATAQUE).exists())  # se guarda tal cual
        r = self.client.get(reverse('agendas_ausencias'))
        self.assertContains(r, ESCAPADO)        # se muestra como texto
        self.assertNotContains(r, ATAQUE)        # nunca como etiqueta ejecutable

    def test_nombre_de_paciente_se_muestra_escapado(self):
        u = self.paciente.usuario
        u.first_name = ATAQUE
        u.save()
        self.client.force_login(u)
        r = self.client.get(reverse('mi_inicio'))
        self.assertContains(r, ESCAPADO)
        self.assertNotContains(r, ATAQUE)

    def test_ninguna_plantilla_desactiva_el_escapado(self):
        """Regla de codificación: no se usa |safe ni {% autoescape off %} en las plantillas."""
        prohibidos = ('|safe', 'autoescape off')
        hallazgos = [f'{p.name}: {t}' for p in Path(settings.BASE_DIR, 'templates').rglob('*.html')
                     for t in prohibidos if t in p.read_text(encoding='utf-8')]
        self.assertEqual(hallazgos, [])
