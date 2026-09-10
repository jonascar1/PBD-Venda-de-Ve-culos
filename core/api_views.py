from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models_usuarios import Usuario, PerfilVendedor
from .models_proposta import Proposta, ContatoAgendado
from .permissions import EhGerente, EhVendedor
from .serializers import (
    UsuarioSerializer,
    PerfilVendedorSerializer,
    CadastroVendedorSerializer,
    EditarAlcadaComissaoSerializer,
)


@api_view(["POST"])
def api_login(request):
    """
    POST { "username": "...", "password": "..." }
    -> { "token": "...", "usuario": {...} }

    Erro genérico de propósito: não revela se foi usuário ou senha errada,
    nem se a conta está desativada.
    """
    username = request.data.get("username", "")
    password = request.data.get("password", "")

    usuario = authenticate(request, username=username, password=password)

    if usuario is None or not usuario.ativo:
        return Response(
            {"detail": "Usuário ou senha inválidos."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token, _ = Token.objects.get_or_create(user=usuario)
    return Response({"token": token.key, "usuario": UsuarioSerializer(usuario).data})


# Nota de instalação (ver README): 'rest_framework.authtoken' precisa estar
# em INSTALLED_APPS, e é necessário rodar migrate depois de adicioná-lo,
# pois ele cria sua própria tabela de tokens.


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_me(request):
    """
    Retorna quem está logado + dados do painel adequado ao perfil.
    O React consulta essa rota uma vez após o login pra saber que tela montar.
    """
    usuario = request.user
    dados = {"usuario": UsuarioSerializer(usuario).data}

    if usuario.is_vendedor():
        perfil_vendedor = PerfilVendedor.objects.filter(usuario=usuario).first()
        propostas = Proposta.objects.filter(vendedor=usuario).order_by("-criada_em")[:10]
        fila_hoje = ContatoAgendado.objects.filter(
            vendedor=usuario, data_prevista=timezone.localdate(), concluido=False
        )
        dados["perfil_vendedor"] = PerfilVendedorSerializer(perfil_vendedor).data if perfil_vendedor else None
        dados["propostas"] = [
            {
                "cliente_nome": p.cliente_nome,
                "veiculo": str(p.veiculo),
                "valor_proposto": p.valor_proposto,
                "desconto_percentual": p.desconto_percentual,
                "status": p.get_status_display(),
            }
            for p in propostas
        ]
        dados["fila_hoje"] = [
            {"cliente_nome": c.cliente_nome, "cliente_contato": c.cliente_contato, "motivo": c.motivo}
            for c in fila_hoje
        ]

    return Response(dados)


from rest_framework import viewsets


class VendedorViewSet(viewsets.ModelViewSet):
    """
    ViewSet = as 5 ações de CRUD (listar, ver um, criar, editar, apagar)
    numa classe só. O router (em api_urls.py) gera as URLs sozinho:

    GET    /api/vendedores/       -> list
    POST   /api/vendedores/       -> create
    GET    /api/vendedores/<id>/  -> retrieve
    PATCH  /api/vendedores/<id>/  -> partial_update
    DELETE /api/vendedores/<id>/  -> destroy (não usamos, ver abaixo)
    """

    queryset = PerfilVendedor.objects.select_related("usuario").all()
    permission_classes = [EhGerente]

    def get_serializer_class(self):
        if self.action == "create":
            return CadastroVendedorSerializer
        if self.action in ("update", "partial_update"):
            return EditarAlcadaComissaoSerializer
        return PerfilVendedorSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        perfil = serializer.save()
        return Response(PerfilVendedorSerializer(perfil).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        # Regra de negócio do T01: nunca apagar vendedor, só desativar.
        # Então "destroy" aqui na verdade desativa (soft delete).
        perfil = self.get_object()
        perfil.usuario.ativo = False
        perfil.usuario.save(update_fields=["ativo"])
        return Response(status=status.HTTP_204_NO_CONTENT)



