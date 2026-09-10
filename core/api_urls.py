from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import api_views

# O Router olha pro ViewSet e gera sozinho todas as URLs de CRUD.
# Se no futuro você criar VeiculoViewSet, PropostaViewSet, etc,
# é só registrar aqui embaixo — uma linha por recurso, sem escrever
# nenhum path() novo na mão.
router = DefaultRouter()
router.register(r"vendedores", api_views.VendedorViewSet, basename="vendedor")

urlpatterns = [
    path("login/", api_views.api_login, name="api_login"),
    path("logout/", api_views.api_logout, name="api_logout"),
    path("me/", api_views.api_me, name="api_me"),
    path("", include(router.urls)),  # inclui todas as rotas geradas pelo router
]
