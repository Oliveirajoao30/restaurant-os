from rest_framework.routers import DefaultRouter

from catalog.interfaces.api.views import MenuItemViewSet

router = DefaultRouter()
router.register('menu-items', MenuItemViewSet, basename='menu-item')

urlpatterns = router.urls
