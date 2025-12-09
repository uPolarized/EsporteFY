from django.apps import AppConfig


class PartidasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'partidas'

    def ready(self):
        import partidas.signals # Importa os nossos sinais

