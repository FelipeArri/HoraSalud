from django import forms
from django.core.exceptions import ValidationError

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


class EnrolamientoForm(IngresoRutForm):
    """B-06: RUT + codigo de un solo uso que entrega el SOME."""

    codigo = forms.CharField(label='Código del SOME', max_length=12)

    def clean_codigo(self):
        codigo = ''.join(c for c in self.cleaned_data['codigo'] if c.isdigit())
        if len(codigo) != 8:
            raise ValidationError('El código tiene 8 números (ej. 1234-5678).')
        return codigo
