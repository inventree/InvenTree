## 3.8 Uso de IA

### Prompts Utilizados

#### Prompt 1: Refinamento Gramatical do Backlog (Fase II)

**Contexto:** Engenharia de Requisitos para CLI com foco na Persona Mariana Souza.

Atue como Engenheiro de Requisitos Sênior. Com base no MVP selecionado ("Padronização e Semântica de Saídas de Erro via CLI com Guia de Resolução Acoplado") , refine as 5 histórias de usuário mapeadas para o escopo.

Certifique-se de aplicar de forma estrita o template tradicional de histórias de usuário: **Como [usuário], quero [ação], para que [benefício]**. Garanta que o benefício esteja conectado diretamente com o ganho de autonomia de Mariana (equipe de suporte) e com o setup rápido de Lucas (desenvolvedor iniciante). 

#### Prompt 2: Detalhamento de Comportamento e Cenários de Teste (Fase II)

**Contexto:** Mapeamento de critérios normativos baseados no comportamento esperado.
  
Para as 5 histórias de usuário refinadas no prompt anterior, desdobre os critérios de aceite obrigatoriamente utilizando a sintaxe BDD: **Dado que... Quando... Então...**.
 
Logo após cada critério, mapeie cenários de teste objetivos seguindo estritamente a classificação do roteiro da disciplina:
* Dados válidos $\rightarrow$ sucesso * Campo vazio / Fluxo alternativo $\rightarrow$ erro * Dados inválidos / Exceção $\rightarrow$ validação falha 
  
Mantenha os cenários de teste focados no contexto técnico e operacional de uma interface de linha de comando (CLI). 

---

### Decisões Justificadas e Avaliação Crítica

A colaboração com o modelo de inteligência artificial na Fase II atuou como um acelerador criativo no desdobramento das histórias e na estruturação dos cenários executáveis. Contudo, a revisão humana final foi aplicada de maneira rigorosa para corrigir falhas conceituais e garantir a aderência ao ecossistema técnico do repositório:

**Adequação Ortográfica e Sintática do Template:** O modelo de IA gerou inicialmente os benefícios das histórias utilizando a conjunção explicativa simplificada "para". Realizamos a adequação manual em todas as sentenças para o termo exato **"para que"**, cumprindo com precisão a checklist gramatical exigida nos critérios de avaliação do trabalho.

**Tradução de Conceitos Web (GUI) para Linha de Comando (CLI):** Ao mapear os cenários de "campo vazio" e "dados inválidos" para as histórias US04 (Formato JSON) e US05 (Coloração do terminal), a IA alucinou propondo fluxos como "deixar caixas de texto vazias" ou "clicar em botões na interface gráfica". Exercemos o papel de revisores técnicos para traduzir essas validações para a realidade de uma CLI, substituindo-as por "ausência de parâmetros/flags obrigatórias na linha de comando" e "execução do comando em emuladores de terminal sem suporte a caracteres ANSI".

**Simplificação e Testabilidade dos Critérios:** O modelo de IA sugeriu blocos extensos e narrativos de pós-condições para os testes. Nós simplificamos as respostas brutas mantendo apenas os comportamentos diretamente observáveis no terminal através de código ou saídas textuais (`stdout`/`stderr`), tornando as asserções objetivas para a fase de implementação prática no Pull Request.