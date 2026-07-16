 # Descrição do Sistema
 
O Inventree é um sistema de gerenciamento de inventario de código aberto, planejado para auxiliar na gestão de estoques. Buscando ser uma alternativa leve e de fácil uso, visando aplicações de pequenas e médias empresas ou para hobby. Utiliza de uma forte logica de negócios para manter o histórico de rastreamento do estoque, para que o usuário tem acesso rápido as informações. 

O sistema é desenvolvido em python e django, armazenando dados em um banco de dados relacional e os disponibiliza através de uma aplicação WEB. Tendo como opção também a integração com outra aplicação através de uma API.        

O sistema possui algumas funcionalidades principais, são elas:

- Parts: É o componente principal do sistema, representam os itens que serão estocados e organizados pelo sistema;
- Suppliers: É uma funcionalidade que tem como função gerenciar fornecedores, podendo realizar operações sobre os fornecedores do usuário;
- Instant Stock Knowledge: Visualizar informações sobre o estoque e as parts, de forma rápida e direta, permitindo filtrar dados e organizar informações;
- Bill of Materials: Gerencia a lista de materiais que uma part precisa para ser criada, assim permitindo criar pedidos para essas;
- Build Parts: É a funcionalidade responsável por rastrear o progresso de construção de novas parts e estoques da mesma;
- Report: É capaz de gerar relatórios baseados nas movimentações realizadas no estoque;

## Qual o problema o sistema resolve  ?

O InvenTree busca atender a demanda sobre um sistema de gerenciamento de estoques de acesso livre que possa ser integrado a outros sistemas de maneira fácil, facilitando assim que pequenas e médias empresas possam gerenciar seus estoques.

## Qual "trabalho" o usuário deseja realizar ?

Quando um usuário precisa gerenciar um estoque com multiplos fornecedores, locais de deposito, peças e sub-peças, ele busca visuabilidade rápida e clara sobre o que está disponivel no estoque e o que precisa ser reposto, caso contrario os processos não sejam interrompidos nem sofram com a falta de algum material que por engano não está disponivel para a tarefa em que ele é necessário 

## Onde há falhas ou oportunidades ? 

O Projeto possui uma label no github, chamada roadmap, onde são categorizados issues que estão no caminho de serem implementadas e priorizadas, além de mais algumas que são adicionadas pela propria comunidade, que revelam pontos a serem resolvidos/aprimorados, podemos citar:

- **Initial Stock Data fields are missing in Add Part form when enabled**
([#12266](https://github.com/inventree/InvenTree/issues/12266)) Mesmo com a opção "Initial stock data" habilitada no painel admin, o formulario de criação de peça não exibe campos para informar o estoque inicial. 

- **Adding/pulling custom status text in printable labels/reports**
([#11973](https://github.com/inventree/InvenTree/issues/11973)) Quando o usuário utiliza status costumizados de estoque, não conseguem "imprimir" o texto descritivo desse status nas tags.

- **Decrementing Non-Tracked Stock When Completing Build Output**
([#11228](https://github.com/inventree/InvenTree/issues/11228)) Em uma ordem de produção de longa duração, o estoque "disponivel" de materia-prima não rastreada não é atualizado corretamente conforme os build outputs, gerando informação impresisa. 
