"""
T01 - Views: login e painel de cada perfil.

Critérios cobertos aqui:
- Login com usuário/senha, erro genérico (não revela se foi usuário ou senha errada)
- O menu/painel mostra só o que o perfil pode usar
- Só gerente edita alçada/comissão
- Abrir pelo endereço uma rota de outro perfil é recusado no servidor
  (via @perfil_requerido, não por esconder link)
"""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .decorators import perfil_requerido
from .models import Usuario, PerfilVendedor


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        usuario = authenticate(request, username=username, password=password)

        # Erro genérico de propósito: não dizer se foi usuário ou senha
        # errada, nem se a conta está desativada — isso é informação
        # que ajuda quem está tentando invadir.
        erro_generico = "Usuário ou senha inválidos."

        if usuario is None or not usuario.ativo:
            messages.error(request, erro_generico)
            return render(request, "core/login.html")

        login(request, usuario)
        return redirect("painel")

    return render(request, "core/login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def painel_view(request):
    """
    Um único ponto de entrada pós-login que redireciona (ou renderiza)
    o painel certo pro perfil do usuário. O template escolhido já
    mostra só as opções daquele perfil — não é a mesma tela com botões
    escondidos via CSS/JS.
    """
    usuario = request.user

    if usuario.is_gerente():
        return redirect("painel_gerente")
    elif usuario.is_vendedor():
        return redirect("painel_vendedor")
    elif usuario.is_administrativo():
        return redirect("painel_administrativo")

    # Perfil não reconhecido: nega por padrão, nunca libera por engano.
    logout(request)
    messages.error(request, "Perfil de usuário inválido. Contate o gerente.")
    return redirect("login")


@perfil_requerido("GERENTE")
def painel_gerente_view(request):
    vendedores = PerfilVendedor.objects.select_related("usuario").all()
    return render(request, "core/painel_gerente.html", {"vendedores": vendedores})


@perfil_requerido("VENDEDOR")
def painel_vendedor_view(request):
    dados = get_object_or_404(PerfilVendedor, usuario=request.user)
    return render(request, "core/painel_vendedor.html", {"dados": dados})


@perfil_requerido("ADMINISTRATIVO")
def painel_administrativo_view(request):
    return render(request, "core/painel_administrativo.html")


@perfil_requerido("GERENTE")
def editar_alcada_comissao_view(request, vendedor_id):
    """
    Único ponto do sistema que altera alçada/comissão.
    Protegido em duas camadas: o decorator (só GERENTE acessa a rota)
    e o clean() do model (só aceita editado_por que seja gerente).
    """
    dados = get_object_or_404(PerfilVendedor, pk=vendedor_id)

    if request.method == "POST":
        dados.alcada_desconto = request.POST.get("alcada_desconto", dados.alcada_desconto)
        dados.percentual_comissao = request.POST.get("percentual_comissao", dados.percentual_comissao)
        dados.editado_por = request.user
        dados.full_clean()  # dispara o clean() do model
        dados.save()
        messages.success(request, "Dados do vendedor atualizados.")
        return redirect("painel_gerente")

    return render(request, "core/editar_alcada_comissao.html", {"dados": dados})