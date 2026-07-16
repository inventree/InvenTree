# Definição do MVP

## Problema
Issue ([#12266](https://github.com/inventree/InvenTree/issues/12266)) Mesmo com a opção "Initial stock data" habilitada no painel admin, o formulario de criação de peça não exibe campos para informar o estoque inicial.

## Solução do Problema (MVP)
Exibir o campo de estoque inicial no formulário de criação de Part quando a opção "Initial stock data" estiver habilitada, eliminando a necessidade do lançamento de estoque manual e separado.

## Descrição do Problema
Ao analizar a branch: `master` encontramos as seguintes informações sobre o problema:
- **Backend:** No backend o campo `initial_stock` já foi criado e implementado, recebendo `quantity` e `location` e criando o `StockItem` junto com a peça.
- **Frontend:** No frontend, o formulário de criação de uma `Part` decide se exibe os campos através o do seguinte trecho de codigo:

```tsx
    // Additional fields for creation
    if (create && !virtual) {
      fields.copy_category_parameters = {};

      if (virtual != false) {
        fields.initial_stock = {
          icon: <IconPackages />,
          children: {
            quantity: {
              value: 0
            },
            location: {}
          }
        };
      }
```
Assim a condição `!virtual` checa se a peça é **virtual**, mas deveria checar se a configuração global `PART_CREATE_INITIAL` está habilitada, como uma peça que não é virtual nunca satisfaz, logo o `initial_stock` nunca é adicionado ao formulário.


## Justificativa de Valor
- Resolver um problema já indicado pela comunidade.
- Escopo pequeno e isolado.
- Impacto direto na experiencia do usuário no fluxo mais básico do sistema

## Justificativa de Viabilidade
- Área do codigo já mapeada
- Não exige mudança de schema de banco de dados
- Testavel de forma isolada

## Relação com o JTBD
Esse MVP atende a necessidade de visibilidade clara e confiança que um gerenciador de estoque precisa ter, reduzindo riscos para que aconteça erros na hora de registrar etoque inicial dado a ação de criar uma nova peça.



