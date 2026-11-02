"""Formularios de B-21 (gestión de agendas)."""
from django import forms

from .models import AusenciaProfesional, PlantillaAgenda


class _Estilo:
    def _estilar(self):
        for campo in self.fields.values():
            es_lista = isinstance(campo.widget, forms.Select)
            campo.widget.attrs.setdefault('class', 'form-select' if es_lista else 'form-control')


class PlantillaForm(_Estilo, forms.ModelForm):
    class Meta:
        model = PlantillaAgenda
        fields = ['especialidad', 'dia_semana', 'hora_inicio', 'hora_fin', 'duracion_min', 'tipo_cupo']
        widgets = {'hora_inicio': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
                   'hora_fin': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._estilar()


class AusenciaForm(_Estilo, forms.ModelForm):
    class Meta:
        model = AusenciaProfesional
        fields = ['profesional', 'desde', 'hasta', 'motivo', 'detalle']
        widgets = {'desde': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
                   'hasta': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profesional'].queryset = (self.fields['profesional'].queryset
                                               .filter(usuario__is_active=True).select_related('usuario'))
        self._estilar()

    def clean(self):
        datos = super().clean()
        if datos.get('desde') and datos.get('hasta') and datos['hasta'] < datos['desde']:
            self.add_error('hasta', 'Debe ser igual o posterior a "desde".')
        return datos
