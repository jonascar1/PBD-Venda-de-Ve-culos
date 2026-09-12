from django.urls import path

from . import views

urlpatterns = [
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("painel/", views.painel_view, name="painel"),
    path("painel/gerente/", views.painel_gerente_view, name="painel_gerente"),
    path("painel/vendedor/", views.painel_vendedor_view, name="painel_vendedor"),
    path("painel/administrativo/", views.painel_administrativo_view, name="painel_administrativo"),
    path("vendedores/<int:vendedor_id>/editar/", views.editar_alcada_comissao_view, name="editar_alcada_comissao"),
]