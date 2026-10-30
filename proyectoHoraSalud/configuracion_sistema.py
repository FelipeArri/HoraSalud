"""
Patron Singleton (D26-C03).

Parametros de negocio unicos del sistema (RN-03, RF-05, RF-06), accesibles
desde cualquier aplicacion sin duplicar valores.
"""


class ConfiguracionSistema:
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia.horizonte_maximo_reserva_dias = 30    # RN-03
            cls._instancia.tolerancia_no_show_minutos = 20       # RF-05
            cls._instancia.plazo_confirmacion_reasignacion_min = 10  # RF-06
            cls._instancia.cancelacion_minima_horas = 2          # RN-04
        return cls._instancia
