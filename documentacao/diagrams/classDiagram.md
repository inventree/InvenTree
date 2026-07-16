# Diagrama de Classes
Baseando-se no MVP proposto para a issue ([#12266](https://github.com/inventree/InvenTree/issues/12266)) obtemos o seguinte diagrama de classe:

```mermaid
    classDiagram
    class Part {
        +int id
        +string name
        +string description
        +bool active
        +bool virtual
        +bool purchaseable
        +int category_id
        +create(data) Part
    }
 
    class StockItem {
        +int id
        +int part_id
        +int location_id
        +decimal quantity
        +datetime creation_date
        +create(part, quantity, location) StockItem
    }
 
    class StockLocation {
        +int id
        +string name
        +int parent_id
    }
 
    class PartCategory {
        +int id
        +string name
        +int parent_id
    }
 
    class InitialStockSerializer {
        +decimal quantity
        +int location
        +validate(data) bool
    }
 
    class PartSerializer {
        +InitialStockSerializer initial_stock
        +create(validated_data) Part
    }
 
    class GlobalSetting {
        +string key
        +string value
        +isSet(key) bool
    }
 
    Part "1" --> "0..*" StockItem : possui
    StockItem "0..*" --> "1" StockLocation : armazenado em
    Part "0..*" --> "1" PartCategory : pertence a
    PartSerializer "1" --> "0..1" InitialStockSerializer : contém
    PartSerializer ..> Part : cria
    PartSerializer ..> StockItem : cria (se initial_stock informado)
    GlobalSetting <.. PartSerializer : consulta PART_CREATE_INITIAL



```