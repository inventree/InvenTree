## 3.6 Cenários de Teste

### US01: Categorização e Estruturação Semântica de Erros
* **História:** Como Analista de Suporte, quero visualizar os erros estruturados por categoria, para que eu possa identificar a origem do problema instantaneamente.
* **Critério:**
  Dado que o sistema sofra uma falha interna de comunicação com a base de dados
  Quando o comando CLI for executado
  Então o terminal deve exibir a saída no padrão rigoroso `[ERRO: <CATEGORIA>] <Mensagem>`
* **Cenários de teste:**
  - Dados válidos → sucesso: Queda do banco simulada gera `[ERRO: BANCO_DE_DADOS] Falha de conexão na porta 5432`
  - Dados inválidos/Exceção não mapeada → validação falha: Erro desconhecido gera `[ERRO: SISTEMA_DESCONHECIDO] Ocorreu uma falha interna inesperada`

### US02: Exibição de Ações Corretivas Sugeridas
* **História:** Como Analista de Suporte, quero receber uma sugestão de comando ou ação de correção junto ao log de erro, para que eu consiga resolver o incidente de forma autônoma.
* **Critério:**
  Dado que um log de erro padronizado seja gerado na CLI
  Quando a categoria possuir uma solução conhecida pré-documentada
  Então o sistema deve exibir uma linha adicional contendo `SUGESTÃO: <Ação corretiva>`
* **Cenários de teste:**
  - Dados válidos → sucesso: Erro de escrita gera `[ERRO: PERMISSAO] Arquivo de config ilegível` seguido de `SUGESTÃO: Execute 'chmod +w <arquivo>'`
  - Campo vazio/Solução indisponível → erro: Erro sem tratativa cadastrada omite a linha de sugestão

### US03: Tratamento de Erros Semânticos no Setup de Ambiente
* **História:** Como Desenvolvedor Iniciante, quero que os erros de setup de ambiente gerem saídas semânticas detalhadas, para que eu não perca tempo com configurações incorretas.
* **Critério:**
  Dado que o desenvolvedor execute o script de inicialização do projeto
  Quando houver uma dependência ou versão de software desatualizada na máquina hospedeira
  Então o script deve interromper a execução e apontar qual dependência causou o problema e a versão mínima exigida
* **Cenários de teste:**
  - Dados inválidos/Ambiente defasado → validação falha: Versão do Node antiga interrompe o fluxo e exibe `[ERRO: AMBIENTE] Versão do Node.js incompatível. Encontrada: v14. Requerida: >= v18`
  - Dados válidos → sucesso: Todas as dependências corretas permitem que o setup finalize com sucesso

### US04: Flag de Saída em Formato Estruturado JSON
* **História:** Como Analista de Suporte, quero poder exportar os erros estruturados em formato JSON usando uma flag `--json`, para que seja possível integrá-los a outras ferramentas de automação.
* **Critério:**
  Dado que qualquer comando da ferramenta CLI resulte em um erro
  Quando o usuário adicionar o parâmetro `--json` ao final da linha de comando
  Então o erro não deve ser impresso em texto comum, mas sim como um objeto JSON válido contendo as chaves `"error"`, `"category"`, `"message"` e `"suggestion"`
* **Cenários de teste:**
  - Dados válidos → sucesso: Comando com erro executado com `--json` retorna estritamente o objeto `{"error": true, "category": "REDE", "message": "Timeout ao conectar na API"}`
  - Campo vazio/Parâmetro ausente → erro: Comando com erro executado sem a flag retorna o log em texto legível padrão da CLI

### US05: Identificação Visual de Erros por Cores no Terminal
* **História:** Como Analista de Suporte, quero que as categorias de erros críticos possuam cores distintas no terminal, para que o diagnóstico sob pressão seja facilitado.
* **Critério:**
  Dado que a CLI esteja rodando em um emulador de terminal compatível com caracteres ANSI
  Quando um erro crítico de infraestrutura for disparado
  Então o prefixo `[ERRO: CATEGORIA]` deve ser renderizado utilizando a cor correspondente ao nível de severidade estabelecido
* **Cenários de teste:**
  - Dados válidos → sucesso: Erro de banco de dados renderiza a tag com o código ANSI para a cor vermelha
  - Dados inválidos/Terminal sem suporte → validação falha: Execução em ambiente sem suporte TTY identifica a limitação e remove os caracteres ANSI, exibindo o texto limpo