---
title: Python Interface Examples
---

## Examples

Following is a *non-exhaustive* list of examples of the capabilities provided by the python library. For a complete look at what it can do, [read the source code](https://github.com/inventree/inventree-python)!

### Creating New Items

Use the `create` method to add new items to the database:

```python
from inventree.part import Part, PartCategory
from inventree.stock import StockItem

## Create a new PartCategory object,
## underneath the existing category with pk 7. Leave the parent empty for a top level category
furniture = PartCategory.create(api, {
    'name': 'Furniture',
    'description': 'Chairs, tables, etc',
    'parent': 7,
})

## Create a new Part
## Use the pk (primary-key) of the newly created category
couch = Part.create(api, {
    'name': 'Couch',
    'description': 'Long thing for sitting on',
    'category': furniture.pk,
    'active': True,
    'virtual': False,
    ## Note - You do not have to fill out *all* fields
})
```

### Updating Attributes

Most model fields which are exposed via the API can be directly edited using the python interface, by simply calling the `save()` method as shown below:

```python
from inventree.api import InvenTreeAPI
from inventree.part import Part

api = InvenTreeAPI(host='http://localhost:8000', username='admin', password='inventree')

# Retrieve part instance with primary-key of 1
part = Part(api, pk=1)

# Update specified part parameters
part.save(data={
    "description": "New part description",
    "minimum_stock": 250,
})

# Reload data from remote server
part.reload()

# Display updated data
print("Part Name:", part.name)
print("Description:", part.description)
print("Minimum stock:", part.minimum_stock)
```

!!! info "Read Only Fields"
    Note that some fields are read-only and cannot be edited via the API

### Adding Parameters

Each [part](../../part/part.md) can have multiple [parameters](../../part/parameter.md). For the example of the sofa (above) *length* and *weight* make sense. Each parameter has a parameter template that combines the parameter name with a unit. So we first have to create the parameter templates and afterwards add the parameter values to the sofa.

```python
from inventree.part import Parameter
from inventree.part import ParameterTemplate

LengthTemplate = ParameterTemplate.create(api, { 'name' : 'Length', 'units' : 'Meters' })
WeightTemplate = ParameterTemplate.create(api, { 'name' : 'Weight', 'units' : 'kg' })

ParameterLength = Parameter.create(api, { 'part': couch.pk, 'template': LengthTemplate.pk, 'data' : 2 })
ParameterWeight = Parameter.create(api, { 'part': couch.pk, 'template': WeightTemplate.pk, 'data' : 60 })
```
These parameter templates need to be defined only once and can be used for all other parts. Lets finally add a picture.

```python
couch.uploadImage('my_nice_couch.jpg')
```

### Adding Location Data

If we have several sofas on stock we need to know there we have stored them. So let’s add stock locations to the part. Stock locations can be organized in a hierarchical manner e.g. boxes in shelves in aisles in rooms. So each location can have a parent. Let’s assume we have 10 sofas in box 12 and 3 sofas in box 13 located in shelve 43 aisle 3. First we have to create the locations, afterwards we can put the sofas inside.

```python

from inventree.stock import StockLocation
from inventree.stock import StockItem

...

## Create the stock locations. Leave the parent empty for top level hierarchy
Aisle3 = StockLocation.create(api, {'name':'Aisle 3','description':'Aisle for sofas','parent':''})
Shelve43 = StockLocation.create(api, {'name':'Shelve 43','description':'Shelve for sofas','parent':Aisle3.pk})
Box12 = StockLocation.create(api, {'name':'Box 12','description':'green box','parent':Shelve43.pk})
Box13 = StockLocation.create(api, {'name':'Box 13','description':'red box','parent':Shelve43.pk})

## Now fill them with items
Id1 = StockItem.create(api, { 'part': sofa.pk, 'quantity': 10, 'notes': 'new ones', 'location': Box12.pk, ‘status’:10 })
Id2 = StockItem.create(api, { 'part': sofa.pk, 'quantity': 3, 'notes': 'old ones', 'location': Box13.pk, ‘status’:55 })

```
Please recognize the different status flags. 10 means OK, 55 means damaged. We have the following choices:

* 10: OK
* 50: Attention needed
* 55: Damaged
* 60: Destroyed
* 65: Rejected
* 70: Lost
* 85: Returned

### Adding Manufacturers and Supplier

We can add manufacturers and suppliers to parts. We first need to create two companies, ACME (manufacturer) and X-Store (supplier).

```python
from inventree.company import Company

...

acme = Company.create(api, {
    'name' : 'ACME',
    'description':'A Company that makes everything',
    'website':'https://www.acme.bla',
    'is_customer':0,
    'is_manufacturer':1,
    'is_supplier':0
})
xstore = Company.create(api, {
    'name' : 'X-Store',
    'description':'A really cool online store',
    'website':'https://www.xst.bla',
    'is_customer':0,
    'is_manufacturer':0,
    'is_supplier':1
})
```

Please recognize the different flag settings for is_supplier and is_manufacturer. Now lets add those to our couch:

```python
from inventree.company import SupplierPart

...

SupplierPart.create(api,{
    'part':couch.pk,
    'supplier':xstore.pk,
    'SKU':'some_code',
    'link':'https://www.xst.bla/products/stock?...'
})
ManufacturerPart.create(api,{
    'part':couch.pk,
    'manufacturer':acme.pk,
    'MPN':'Part code of the manufacturer'
})
```

### Stock Adjustments

Various stock adjustment actions can be performed as follows:

```python
from inventree.stock import StockItem, StockLocation

# Fetch item from the server
item = StockItem(api, pk=99)

# Count stock
item.countStock(500)

# Add stock to the item
item.addStock(15)

# Remove stock from the item
item.removeStock(25)

# Transfer partial quantity to another location
loc = StockLocation(api, pk=12)
item.transferStock(loc, quantity=50)
```

### Delete a Part

To delete a [Part instance](../../part/part.md), first in needs to be marked as *inactive* (otherwise it will throw an error):

```python
from inventree.part import Part

part = Part(api, pk=10)
part.save(data={'active': False})
part.delete()
```

### Bulk Delete

Some database models support bulk delete operations, where multiple database entries can be deleted in a single API query.

```python
from inventree.stock import StockItem

# Delete all items in a particular category
StockItem.bulkDelete(api, filters={'category': 3})
```

### Upload Attachments

We have the possibility to upload attachments against a particular Part. We can use pdf for documents but also other files like 3D drawings or pictures. To do so we add the following commands:

```python
from inventree.part import PartAttachment

# The ID of the Part to attach the files to
part_id = 47

PartAttachment.upload(api, part_id, 'manual.pdf', comment='Datasheet')
PartAttachment.upload(api, part_id, 'sofa.dxf', comment='Drawing')
```

Alternatively, we can upload an attachment directly against the `Part` instance:

```python
from inventree.part import Part

part = Part(api, pk=47)

part.uploadAttachment('data.txt', comment='A data file')
```

### Adding a Bill of Materials

Imagine your sofa is made from three parts: one seat, one back and two arm rests. To enable this
the assembly flag of the sofa part has to be set. You need to have all three parts in you InvenTree
database.

A BOM (Bill of Materials) contains BOM items. These are separate records in the database that refer to the master assembly (the *part*)
and the component which is being used (the *sub_part*).

BOM Items can be created using the Python API interface as follows:

```python
BomItem.create(api, data={'part':sofa_id, 'sub_part':back_id, 'quantity':1, 'reference':'p1'})
BomItem.create(api, data={'part':sofa_id, 'sub_part':seat_id, 'quantity':1, 'reference':'p2'})
BomItem.create(api, data={'part':sofa_id, 'sub_part':armrest_id, 'quantity':2, 'reference':'p3, p4'})
```

Now you have three BOM items that make the BOM for the sofa. The `id` values are the primary keys of the
specified parts. The reference can be any string that names the instances.
