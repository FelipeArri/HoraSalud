"""
Router de bases de datos: todo lo de fonasaSimuladoApp va a la base 'fonasa'
(fonasa_simulado); todo lo demas a 'default' (horasalud_db). Asi quedan como
dos sistemas separados, igual que en la realidad.
"""
APP = 'fonasaSimuladoApp'
BASE = 'fonasa'


class RouterFonasa:
    def db_for_read(self, model, **hints):
        return BASE if model._meta.app_label == APP else None

    def db_for_write(self, model, **hints):
        return BASE if model._meta.app_label == APP else None

    def allow_relation(self, obj1, obj2, **hints):
        # No hay relaciones entre HoraSalud y FONASA: son sistemas distintos
        if APP in (obj1._meta.app_label, obj2._meta.app_label):
            return obj1._meta.app_label == obj2._meta.app_label
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == APP:
            return db == BASE
        if db == BASE:
            return False  # en fonasa_simulado solo van las tablas de FONASA
        return None
