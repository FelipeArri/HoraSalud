from django import forms
from django.core.exceptions import ValidationError

from agendaApp.models import Especialidad

from .models import Sector, Usuario
from .validators import normalizar_rut, validar_rut


class IngresoRutForm(forms.Form):
    """RF-01: el RUT se valida (formato y digito verificador) antes de buscarlo."""

    rut = forms.CharField(
        label='RUT', max_length=12,
        widget=forms.TextInput(attrs={
            'placeholder': '12.345.678-9', 'autocomplete': 'username', 'autofocus': True,
            'inputmode': 'text', 'class': 'form-control form-control-lg campo-rut',
        }))

    def clean_rut(self):
        rut = normalizar_rut(self.cleaned_data['rut'])
        if rut and '-' not in rut and len(rut) > 1:
            rut = f'{rut[:-1]}-{rut[-1]}'  # acepta 123456789 sin guion
        try:
            validar_rut(rut)
        except ValidationError:
            raise ValidationError('Revisa tu RUT: el número o el dígito verificador no es correcto.')
        return rut


class IngresoPersonalForm(IngresoRutForm):
    """B-20: el personal del CESFAM entra con RUT + clave."""

    clave = forms.CharField(label='Clave', strip=False, widget=forms.PasswordInput(attrs={
        'autocomplete': 'current-password', 'class': 'form-control form-control-lg'}))


class TutorForm(IngresoRutForm):
    """B-10 · RF-03: RUT y nombre de la persona que será tutor."""

    nombres = forms.CharField(label='Nombres', max_length=150, required=False,
                              widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    apellidos = forms.CharField(label='Apellidos', max_length=150, required=False,
                                widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    confirmo = forms.BooleanField(
        label='Entiendo que esta persona podrá pedir y cancelar horas por mí.',
        error_messages={'required': 'Confirma que autorizas a esta persona.'})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rut'].label = 'RUT del tutor'
        self.fields['rut'].widget.attrs['autocomplete'] = 'off'
        self.fields['rut'].widget.attrs.pop('autofocus', None)


class FuncionarioForm(IngresoRutForm):
    """B-20: el Administrador CESFAM agrega a un funcionario (y confirma con SU clave)."""

    TIPOS = [(t.value, t.label) for t in (Usuario.Tipo.ADMINISTRATIVO, Usuario.Tipo.PROFESIONAL,
                                           Usuario.Tipo.ADMINISTRADOR)]

    nombres = forms.CharField(max_length=150)
    apellidos = forms.CharField(max_length=150)
    tipo = forms.ChoiceField(label='Cargo', choices=TIPOS)
    especialidad = forms.ModelChoiceField(label='Especialidad o programa', required=False,
                                          queryset=Especialidad.objects.order_by('nombre'),
                                          empty_label='— (solo para profesionales) —')
    box = forms.CharField(label='Box de atención', max_length=10, required=False)
    sector = forms.ModelChoiceField(label='Sector que atiende', required=False,
                                    queryset=Sector.objects.order_by('nombre'),
                                    empty_label='Todos los sectores')  # DEF-06
    email = forms.EmailField(label='Correo (opcional)', required=False)
    clave_admin = forms.CharField(label='Tu clave de administrador', strip=False,
                                  widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rut'].widget.attrs.pop('autofocus', None)
        self.fields['rut'].widget.attrs['class'] = 'form-control campo-rut'
        for nombre, campo in self.fields.items():
            if nombre != 'rut':
                campo.widget.attrs.setdefault('class', 'form-select' if nombre in ('tipo', 'especialidad', 'sector')
                                              else 'form-control')

    def clean(self):
        datos = super().clean()
        if datos.get('tipo') == Usuario.Tipo.PROFESIONAL and not datos.get('especialidad'):
            self.add_error('especialidad', 'Elige la especialidad o programa del profesional.')
        return datos


class ConfirmarAdminForm(forms.Form):
    """B-20: reautenticación antes de una acción sensible sobre otra cuenta."""

    clave_admin = forms.CharField(label='Tu clave de administrador', strip=False,
                                  widget=forms.PasswordInput(attrs={'autocomplete': 'current-password',
                                                                    'class': 'form-control'}))
    motivo = forms.CharField(label='Motivo (opcional)', max_length=150, required=False,
                             widget=forms.TextInput(attrs={'class': 'form-control'}))


class EnrolamientoForm(IngresoRutForm):
    """B-06: RUT + codigo de un solo uso que entrega el SOME."""

    codigo = forms.CharField(label='Código del SOME', max_length=12)

    def clean_codigo(self):
        codigo = ''.join(c for c in self.cleaned_data['codigo'] if c.isdigit())
        if len(codigo) != 8:
            raise ValidationError('El código tiene 8 números (ej. 1234-5678).')
        return codigo
