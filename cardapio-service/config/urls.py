from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('catalog.interfaces.api.urls')),
    path('', include('catalog.interfaces.web.urls')),
]
