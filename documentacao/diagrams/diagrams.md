# 3.9 / 3.10 — Modelagem UML

Ferramenta: **Mermaid**

MVP: Padronização e Semântica de Saídas de Erro via CLI com Guia de Resolução Acoplado

Os diagramas combrem principalmente o fluxo de **US01**, que é implementado no PR 

---

## Diagrama de Classes 
```mermaid
classDiagram
    class ErrorCategory {
        <<enumeration>>
        BANCO_DE_DADOS
        REDE
        PERMISSAO
        AMBIENTE
        SISTEMA_DESCONHECIDO
    }
 
    class StructuredError {
        +ErrorCategory category
        +str message
        +str suggestion
        +Exception raw_exception
    }
 
    class ExceptionCategorizer {
        +classify(exc: Exception) ErrorCategory
    }
 
    class SuggestionProvider {
        -dict~ErrorCategory, str~ suggestions_map
        +get_suggestion(category: ErrorCategory) str
    }
 
    class OutputFormatter {
        <<interface>>
        +format(error: StructuredError) str
    }
 
    class TextFormatter {
        +format(error: StructuredError) str
    }
 
    class JSONFormatter {
        +format(error: StructuredError) str
    }
 
    class ColorSupportDetector {
        +is_tty_supported() bool
    }
 
    class AnsiColorMapper {
        -dict~ErrorCategory, str~ color_map
        +get_color(category: ErrorCategory) str
    }
 
    class CLIErrorHandler {
        -ExceptionCategorizer categorizer
        -SuggestionProvider suggestion_provider
        -ColorSupportDetector tty_detector
        -AnsiColorMapper color_mapper
        +handle(exc: Exception, json_flag: bool) None
        -build_structured_error(exc: Exception) StructuredError
        -select_formatter(json_flag: bool) OutputFormatter
    }
 
    class CLIEntryPoint {
        <<existing - tasks.py / invoke>>
        +run_command(args) None
    }
 
    OutputFormatter <|.. TextFormatter
    OutputFormatter <|.. JSONFormatter
    CLIErrorHandler --> ExceptionCategorizer
    CLIErrorHandler --> SuggestionProvider
    CLIErrorHandler --> ColorSupportDetector
    CLIErrorHandler --> AnsiColorMapper
    CLIErrorHandler --> OutputFormatter
    CLIErrorHandler ..> StructuredError : cria
    ExceptionCategorizer ..> ErrorCategory : retorna
    CLIEntryPoint --> CLIErrorHandler : delega exceções
```
- `ExceptionCategorizer` concentra a lógica da **US01** (categorização).
- `SuggestionProvider` é o ponto de extensão da **US02**.
- `TextFormatter`/`JSONFormatter` (padrão Strategy) resolvem a **US04** (flag `--json`) sem duplicar lógica de formatação.
- `ColorSupportDetector` + `AnsiColorMapper` cobrem a **US05**, isolando a checagem de TTY (evita "vazar" ANSI em terminais sem suporte, conforme o cenário de teste).
- `CLIEntryPoint` representa o ponto de integração real no fork (ex.: `tasks.py`/`invoke`), sem precisar ser reescrito — ele só passa a delegar exceções para `CLIErrorHandler`.



---

## Diagrama de Sequencia

```mermaid
    sequenceDiagram
    actor Usuario as Analista de Suporte
    participant CLI as CLIEntryPoint
    participant Handler as CLIErrorHandler
    participant Categorizer as ExceptionCategorizer
    participant Suggestion as SuggestionProvider
    participant TTY as ColorSupportDetector
    participant Formatter as OutputFormatter
    participant Terminal as Terminal (stdout)
 
    Usuario->>CLI: executa comando (ex: inventree migrate)
    CLI->>CLI: try / executa lógica do comando
    CLI-->>Handler: exceção capturada (raw_exception)
 
    Handler->>Categorizer: classify(exc)
    Categorizer-->>Handler: ErrorCategory (ex: BANCO_DE_DADOS)
 
    Handler->>Suggestion: get_suggestion(category)
    Suggestion-->>Handler: texto da sugestão (ou None)
 
    Handler->>Handler: build_structured_error(exc, category, suggestion)
 
    alt flag --json presente
        Handler->>Formatter: select_formatter(json_flag=true) -> JSONFormatter
    else saída padrão em texto
        Handler->>Formatter: select_formatter(json_flag=false) -> TextFormatter
        Handler->>TTY: is_tty_supported()
        TTY-->>Handler: true / false
    end
 
    Formatter-->>Handler: string formatada
    Handler->>Terminal: escreve saída ([ERRO: CATEGORIA] ... ou JSON)
    Terminal-->>Usuario: exibe erro estruturado (+ sugestão, + cor se aplicável)
```

---

## Diagrama de Componentes

```mermaid
    graph TD
        subgraph CLI_Existente["CLI existente do InvenTree (fork)"]
            A[CLIEntryPoint<br/>tasks.py / invoke commands]
        end
    
        subgraph Novo_Modulo["Novo módulo: cli_error_handling"]
            B[CLIErrorHandler<br/>orquestrador]
            C[ExceptionCategorizer]
            D[SuggestionProvider]
            E[OutputFormatter<br/>Text / JSON]
            F[ColorSupportDetector +<br/>AnsiColorMapper]
        end
    
        G[(Terminal / stdout)]
    
        A -- "exceção não tratada" --> B
        B --> C
        B --> D
        B --> E
        B --> F
        E --> G
        F -.->|"aplica cor se TTY suportar"| E
    
        style Novo_Modulo fill:#f5f5f5,stroke:#333,stroke-dasharray: 4 4
```
- O componente `cli_error_handling` é **novo** e isolado — não altera a lógica de negócio existente do InvenTree, apenas intercepta exceções não tratadas na camada de CLI, conforme justificado em `definicao_do_mvp` ("não demanda refatorações na lógica central de negócios").
- Essa separação em componente próprio facilita o PR: o diff fica concentrado em um módulo novo + um ponto de integração mínimo no `CLIEntryPoint`.
