

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ErrorCategory(str, Enum):
    

    BANCO_DE_DADOS = 'BANCO_DE_DADOS'
    REDE = 'REDE'
    PERMISSAO = 'PERMISSAO'
    AMBIENTE = 'AMBIENTE'
    SISTEMA_DESCONHECIDO = 'SISTEMA_DESCONHECIDO'



_DEFAULT_MESSAGES = {
    ErrorCategory.SISTEMA_DESCONHECIDO: 'Ocorreu uma falha interna inesperada',
}


_SUGGESTIONS = {
    ErrorCategory.PERMISSAO: "Execute 'chmod +w <arquivo>' ou ajuste as permissoes do diretorio",
    ErrorCategory.AMBIENTE: "Execute 'invoke install' para reinstalar as dependencias corretas",
    ErrorCategory.BANCO_DE_DADOS: 'Verifique se o servico de banco de dados esta ativo e acessivel',
    ErrorCategory.REDE: 'Verifique a conectividade de rede e as credenciais do endpoint remoto',
}


@dataclass
class StructuredError:
   

    category: ErrorCategory
    message: str
    suggestion: Optional[str] = None


class ExceptionCategorizer:
    
    _TYPE_NAME_MAP = {
        'OperationalError': ErrorCategory.BANCO_DE_DADOS,
        'InterfaceError': ErrorCategory.BANCO_DE_DADOS,
        'DatabaseError': ErrorCategory.BANCO_DE_DADOS,
        'PermissionError': ErrorCategory.PERMISSAO,
        'ModuleNotFoundError': ErrorCategory.AMBIENTE,
        'ImportError': ErrorCategory.AMBIENTE,
        'ConnectionError': ErrorCategory.REDE,
        'ConnectionRefusedError': ErrorCategory.REDE,
        'TimeoutError': ErrorCategory.REDE,
        'URLError': ErrorCategory.REDE,
    }

    
    _KEYWORD_MAP = (
        (('porta', 'connection refused', 'database', 'banco de dados'), ErrorCategory.BANCO_DE_DADOS),
        (('network', 'rede', 'timeout', 'dns'), ErrorCategory.REDE),
        (('permission', 'permissao', 'read-only', 'access is denied'), ErrorCategory.PERMISSAO),
    )

    def classify(self, exc: BaseException) -> ErrorCategory:
        
        type_name = type(exc).__name__
        if type_name in self._TYPE_NAME_MAP:
            return self._TYPE_NAME_MAP[type_name]

        message = str(exc).lower()
        for keywords, category in self._KEYWORD_MAP:
            if any(keyword in message for keyword in keywords):
                return category

        return ErrorCategory.SISTEMA_DESCONHECIDO


class SuggestionProvider:
    

    def get_suggestion(self, category: ErrorCategory) -> Optional[str]:
       
        return _SUGGESTIONS.get(category)


def build_structured_error(
    exc: BaseException,
    categorizer: Optional[ExceptionCategorizer] = None,
    suggestion_provider: Optional[SuggestionProvider] = None,
) -> StructuredError:
    
    categorizer = categorizer or ExceptionCategorizer()
    suggestion_provider = suggestion_provider or SuggestionProvider()

    category = categorizer.classify(exc)
    message = str(exc).strip() or _DEFAULT_MESSAGES.get(
        category, 'Ocorreu uma falha inesperada'
    )

    return StructuredError(
        category=category,
        message=message,
        suggestion=suggestion_provider.get_suggestion(category),
    )


def format_structured_error(error: StructuredError) -> str:
    
    lines = [f'[ERRO: {error.category.value}] {error.message}']
    if error.suggestion:
        lines.append(f'SUGESTAO: {error.suggestion}')
    return '\n'.join(lines)