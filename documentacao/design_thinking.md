# Design Thinking com IA

Este documento apresenta as personas e o mapa de empatia.

## 1. Personas
### Persona 1: Lucas Rocha (O Desenvolvedor Iniciante)
* **Perfil:** Estudante de Sistemas de Informação, 21 anos, usuário de Linux (Ubuntu).
* **Comportamento:** Muito ativo em comunidades de tecnologia no Discord, prefere utilizar ferramentas via linha de comando (CLI) e busca fazer sua primeira contribuição em um projeto open-source para melhorar o currículo.
* **Frustrações/Dores:** Sente que o processo de setup inicial e a documentação do repositório são confusos. Perdeu mais de duas horas tentando rodar o projeto localmente devido a dependências desatualizadas e erros de ambiente não documentados no `README.md`.
* **Objetivos/Ganhos:** Encontrar um guia claro "passo a passo" ou uma automação (como um container Docker ou script de ambiente) que permita configurar o projeto em menos de 10 minutos, dando segurança para codificar.

### Persona 2: Mariana Souza (A Analista de Suporte)
* **Perfil:** Analista de Suporte Técnico, 33 anos, focada em agilidade e cumprimento de prazos.
* **Comportamento:** Pragmática, utiliza o sistema diariamente em ambiente de produção para resolver problemas de clientes sob pressão. Não busca customizar o código, precisa apenas que a ferramenta funcione sem surpresas.
* **Frustrações/Dores:** O sistema gera logs de erro extremamente genéricos no terminal quando algo falha. Quando um processo trava, ela não consegue identificar rapidamente se o problema é de rede, permissão ou um bug interno, atrasando o atendimento.
* **Objetivos/Ganhos:** Obter um formato de logs de erro mais descritivo, limpo e estruturado, facilitando o diagnóstico rápido de falhas sem a necessidade de abrir o código-fonte para entender o problema.

---

## 2. Mapa de Empatia (Persona Principal: Mariana Souza)

| O que ela Pensa e Sente? | O que ela Vê? |
| :--- | :--- |
| * "Preciso resolver os chamados dos clientes rápido."<br>* Frustração com a falta de clareza do sistema.<br>* Insegurança ao tentar adivinhar a causa de um erro. | * Logs extensos e poluídos no terminal.<br>* Clientes cobrando soluções rápidas.<br>* Issues antigas no GitHub discutindo erros parecidos. |
| **O que ela Ouve?** | **O que ela Fala e Faz?** |
| * Os clientes reclamando da demora no suporte.<br>* A gerência cobrando agilidade nas métricas.<br>* Colegas dizendo que o sistema é "caixa preta". | * Reclama que os logs atuais não ajudam em nada.<br>* Abre o terminal e tenta reiniciar o sistema do zero.<br>* Documenta manualmente os erros que consegue decifrar. |
| **Dores (Frustrações)** | **Ganhos (Necessidades/Desejos)** |
| * Perda de tempo decifrando mensagens genéricas.<br>* Estresse com a pressão do tempo de atendimento.<br>* Dependência de desenvolvedores seniores para bugs simples. | * Diagnóstico visual imediato do problema através do log.<br>* Maior autonomia no trabalho diário de suporte.<br>* Redução do tempo de resolução de chamados (SLA). |

---

## 3. Ideias de Solução Exploradas

* **Ideia 1:** Criar um painel visual (Dashboard) para monitoramento de erros em tempo real.
* **Ideia 2:** Padronizar e reestruturar as saídas de erro do sistema de forma semântica (Ex: `[ERRO: BANCO_DE_DADOS] Falha de conexão na porta 5432`) acompanhadas de possíveis ações de correção (Foco selecionado para o MVP).

## 3.3 Prompts Utilizados para a IA

#### Prompt 1: Criação de Personas e Mapa de Empatia

Atue como um especialista em Product Discovery e Design Thinking aplicado à Engenharia de Software. Estou trabalhando em um projeto prático de reformulação e melhoria de uma ferramenta de software livre puramente técnica, baseada em CLI (Interface de Linha de Comando). 

Preciso que você crie 2 personas distintas que representem os usuários desse ecossistema:
1. Um usuário extremo focado no desenvolvimento (ex: um desenvolvedor iniciante ou adotante inicial tentando configurar o ambiente).
2. Um usuário de ponta focado na operação/suporte diário (ex: um analista de suporte sob pressão).

Para cada persona, forneça: Perfil, Comportamento, Frustrações/Dores e Objetivos/Ganhos. 

Em seguida, monte um Mapa de Empatia em formato de tabela Markdown focado na segunda persona (Analista de Suporte), dividindo em: O que ela Pensa e Sente?, O que ela Vê?, O que ela Ouve?, O que ela Fala e Faz?, Dores (Frustrações) e Ganhos (Necessidades/Desejos).

#### Prompt 2: Brainstorming e Ideação de Soluções

Com base nas dores apresentadas pela persona Mariana Souza (Analista de Suporte), especificamente sobre a dificuldade de diagnosticar falhas operacionais devido a logs extensos, poluídos e extremamente genéricos no terminal, sugira ideias de soluções. 

Gere duas propostas distintas: uma que envolva uma quebra de paradigma visual (Dashboard) e outra focada em reestruturação semântica diretamente na linha de comando (CLI) que traga ações de correção acopladas ao erro.

## 4. Reflexão Crítica

O uso da inteligência artificial foi fundamental para acelerar o processo criativo e estruturar o mapeamento psicográfico das personas de forma rápida. O modelo foi capaz de simular com precisão dores reais de profissionais de suporte que lidam com ferramentas open-source.

No entanto, exercemos a decisão humana final ao filtrar alucinações do modelo. A IA sugeriu inicialmente dores voltadas a interfaces mobile e relatórios em PDF, recursos que não condizem com a proposta puramente técnica via CLI do software analisado. Nós removemos esses excessos e refinamos os textos manualmente para garantir que o mapa de empatia estivesse perfeitamente conectado às issues e limitações reais encontradas no repositório do projeto.