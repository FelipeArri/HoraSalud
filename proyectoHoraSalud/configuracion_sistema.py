"""
Patron Singleton (D26-C03).

Parametros de negocio unicos del sistema (RN-03, RF-05, RF-06), accesibles
desde cualquier aplicacion sin duplicar valores.

B-14 (RN-17): los tramos de la lista de espera son PARAMETROS A CALIBRAR.
Son supuestos iniciales; se revisan con las estadisticas de uso (pantalla
"Indicadores de la lista de espera") y se cambian aqui, en una sola linea.
"""


class ConfiguracionSistema:
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia.horizonte_maximo_reserva_dias = 30    # RN-03
            cls._instancia.tolerancia_no_show_minutos = 20       # RF-05
            cls._instancia.cancelacion_minima_horas = 2          # RN-04
            # ---- RF-06 / RN-17: lista de espera ----
            # Mas de 48 h antes de la hora: se ofrece en orden, con 1 hora para responder.
            cls._instancia.lista_tramo_largo_horas = 48
            cls._instancia.plazo_tramo_largo_min = 60
            # Entre 24 y 48 h: se ofrece en orden, con 10 minutos para responder.
            cls._instancia.lista_tramo_corto_horas = 24
            cls._instancia.plazo_confirmacion_reasignacion_min = 10
            # Menos de 24 h (o No-Show): el cupo pasa a la ventanilla del SOME.
            # Los avisos solo se envian en este horario (no se despierta a nadie).
            cls._instancia.avisos_desde_hora = 8
            cls._instancia.avisos_hasta_hora = 20
            # Despues de esta cantidad de ofertas seguidas sin respuesta, el SOME ve una
            # marca para llamar al paciente. El paciente NO pierde su lugar.
            cls._instancia.ofertas_sin_respuesta_alerta = 3
        return cls._instancia
