"""Tests for cli_error_handling.py (US01 / US02).

These mirror the test scenarios documented in
documentacao/cenarios_de_teste.
"""

from cli_error_handling import (
    ErrorCategory,
    build_structured_error,
    format_structured_error,
)


class FakeOperationalError(Exception):
    """Stand-in for a DB driver's OperationalError (avoids a psycopg2 dependency in tests)."""


FakeOperationalError.__name__ = 'OperationalError'


def test_us01_dados_validos_categoriza_erro_de_banco():
    """Cenario: queda do banco simulada -> [ERRO: BANCO_DE_DADOS] ..."""
    exc = FakeOperationalError('Falha de conexao na porta 5432')
    result = build_structured_error(exc)

    assert result.category == ErrorCategory.BANCO_DE_DADOS
    output = format_structured_error(result)
    assert output.startswith('[ERRO: BANCO_DE_DADOS] Falha de conexao na porta 5432')


def test_us01_excecao_nao_mapeada_cai_em_sistema_desconhecido():
    """Cenario: erro desconhecido -> [ERRO: SISTEMA_DESCONHECIDO] ..."""
    exc = RuntimeError('')  # sem mensagem, tipo nao mapeado
    result = build_structured_error(exc)

    assert result.category == ErrorCategory.SISTEMA_DESCONHECIDO
    assert format_structured_error(result) == (
        '[ERRO: SISTEMA_DESCONHECIDO] Ocorreu uma falha interna inesperada'
    )


def test_us02_categoria_com_solucao_conhecida_exibe_sugestao():
    """Cenario: erro de escrita -> linha SUGESTAO: ... e' anexada."""
    exc = PermissionError('Arquivo de config ilegivel')
    result = build_structured_error(exc)
    output = format_structured_error(result)

    assert output == (
        '[ERRO: PERMISSAO] Arquivo de config ilegivel\n'
        "SUGESTAO: Execute 'chmod +w <arquivo>' ou ajuste as permissoes do diretorio"
    )


def test_us02_categoria_sem_solucao_omite_linha_de_sugestao():
    """Cenario: erro sem tratativa cadastrada -> omite a linha de sugestao."""
    exc = RuntimeError('falha nao mapeada qualquer')
    result = build_structured_error(exc)
    output = format_structured_error(result)

    assert 'SUGESTAO' not in output


def test_ambiente_reaproveita_categoria_ja_tratada_pelo_task_exception_handler():
    """ModuleNotFoundError ja era tratado manualmente em tasks.py; garante
    que a nova categorizacao cobre o mesmo caso sem duplicar logica.
    """
    exc = ModuleNotFoundError("No module named 'invoke'")
    result = build_structured_error(exc)

    assert result.category == ErrorCategory.AMBIENTE