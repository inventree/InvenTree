# Diagrama de Componentes
aseando-se no MVP proposto para a issue ([#12266](https://github.com/inventree/InvenTree/issues/12266)) obtemos o seguinte diagrama de componentes:

```mermaid
    graph TB
    subgraph Frontend["Frontend (React)"]
        PartForm["PartForm.tsx<br/>(formulário Add Part)"]
        GlobalSettingsHook["useGlobalSettingsState<br/>(hook de configurações)"]
    end
 
    subgraph Backend["Backend (Django REST Framework)"]
        PartAPI["PartList / PartDetail<br/>(API View)"]
        PartSerializerC["PartSerializer"]
        InitialStockSerializerC["InitialStockSerializer"]
        SettingsAPI["InvenTreeSetting<br/>(PART_CREATE_INITIAL)"]
    end
 
    subgraph Data["Camada de Dados"]
        PartTable[("Tabela: part_part")]
        StockItemTable[("Tabela: stock_stockitem")]
        SettingsTable[("Tabela: common_inventreesetting")]
    end
 
    PartForm -->|consulta configuração| GlobalSettingsHook
    GlobalSettingsHook -->|GET /api/settings/global/| SettingsAPI
    SettingsAPI --> SettingsTable
 
    PartForm -->|POST /api/part/| PartAPI
    PartAPI --> PartSerializerC
    PartSerializerC --> InitialStockSerializerC
    PartSerializerC -->|cria| PartTable
    InitialStockSerializerC -->|cria| StockItemTable
 
    style PartForm fill:#ffd6d6,stroke:#c0392b,stroke-width:2px
    style GlobalSettingsHook fill:#ffd6d6,stroke:#c0392b,stroke-width:2px

```