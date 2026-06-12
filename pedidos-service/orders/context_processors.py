from django.conf import settings


def cardapio_service_url(request):
    """Disponibiliza a URL pública do cardapio-service para os templates (link no menu)."""
    return {'CARDAPIO_SERVICE_URL': settings.CARDAPIO_SERVICE_URL}
