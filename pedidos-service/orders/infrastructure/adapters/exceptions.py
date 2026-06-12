class CatalogServiceUnavailableError(Exception):
    """O cardapio-service não respondeu, demorou demais ou retornou um erro inesperado."""


class MenuItemNotFoundError(Exception):
    """O item solicitado não existe no cardápio (cardapio-service)."""
