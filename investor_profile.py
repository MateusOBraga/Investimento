"""
investor_profile.py
Questionário simples para estimar o perfil de investidor (conservador,
moderado ou arrojado) e sugerir parâmetros de análise compatíveis.

Isso é só uma estimativa educacional simplificada — não substitui o
questionário de suitability (API) que corretoras aplicam por exigência da CVM.
"""

PERGUNTAS = [
    {
        "id": "horizonte",
        "pergunta": "Por quanto tempo você pretende deixar o dinheiro investido?",
        "opcoes": {
            "Menos de 1 ano": 1,
            "De 1 a 3 anos": 2,
            "De 3 a 5 anos": 3,
            "Mais de 5 anos": 4,
        },
    },
    {
        "id": "queda",
        "pergunta": "Se sua carteira caísse 20% em um mês, o que você faria?",
        "opcoes": {
            "Venderia tudo imediatamente": 1,
            "Venderia uma parte": 2,
            "Manteria e esperaria": 3,
            "Compraria mais, aproveitando o preço baixo": 4,
        },
    },
    {
        "id": "experiencia",
        "pergunta": "Qual sua experiência com investimentos em ações?",
        "opcoes": {
            "Nenhuma, estou começando agora": 1,
            "Pouca, já investi algumas vezes": 2,
            "Moderada, invisto com regularidade": 3,
            "Bastante, acompanho o mercado de perto": 4,
        },
    },
    {
        "id": "objetivo",
        "pergunta": "Qual seu principal objetivo?",
        "opcoes": {
            "Preservar o dinheiro, ganhar pouco acima da poupança": 1,
            "Um equilíbrio entre segurança e crescimento": 2,
            "Crescer o patrimônio no médio prazo": 3,
            "Buscar o maior retorno possível, aceitando risco": 4,
        },
    },
]


def calcular_perfil(respostas: dict) -> dict:
    """
    respostas: dict {id_pergunta: valor (1 a 4)}
    Retorna o perfil estimado e sugestões de configuração para o app.
    """
    pontos = sum(respostas.values())
    maximo = len(PERGUNTAS) * 4
    pct = pontos / maximo if maximo else 0

    if pct <= 0.45:
        perfil = "Conservador"
        peso_tecnico_sugerido = 0.3
        descricao = (
            "Você prioriza segurança. Vale focar em ações pagadoras de "
            "dividendos, com baixo endividamento e menor volatilidade — mesmo "
            "que isso signifique abrir mão de ganhos mais explosivos."
        )
        filtro_sugerido = {"dy_min": 5.0, "score_min": 55}
    elif pct <= 0.75:
        perfil = "Moderado"
        peso_tecnico_sugerido = 0.5
        descricao = (
            "Você busca um equilíbrio entre segurança e crescimento. Vale "
            "diversificar entre ações mais estáveis e algumas com potencial "
            "de valorização maior."
        )
        filtro_sugerido = {"dy_min": 2.0, "score_min": 50}
    else:
        perfil = "Arrojado"
        peso_tecnico_sugerido = 0.7
        descricao = (
            "Você tolera mais oscilação em troca de potencial de retorno "
            "maior. Vale prestar atenção em momentum (tendência, RSI, MACD) "
            "além dos fundamentos."
        )
        filtro_sugerido = {"dy_min": 0.0, "score_min": 60}

    return {
        "perfil": perfil,
        "pontuacao": pontos,
        "pontuacao_maxima": maximo,
        "peso_tecnico_sugerido": peso_tecnico_sugerido,
        "descricao": descricao,
        "filtro_sugerido": filtro_sugerido,
    }
