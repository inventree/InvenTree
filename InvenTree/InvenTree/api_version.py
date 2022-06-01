"""
InvenTree API version information
"""


# InvenTree API version
INVENTREE_API_VERSION = 54

"""
Increment this API version number whenever there is a significant change to the API that any clients need to know about

v54 -> 2022-06-01 : https://github.com/inventree/InvenTree/pull/2934
    - Converting more server-side actions to use the API
    - Build orders can now be deleted via the API

v53 -> 2022-06-01 : https://github.com/inventree/InvenTree/pull/3110
    - Adds extra search fields to the BuildOrder list API endpoint

v52 -> 2022-05-31 : https://github.com/inventree/InvenTree/pull/3103
    - Allow part list API to be searched by supplier SKU

v51 -> 2022-05-24 : https://github.com/inventree/InvenTree/pull/3058
    - Adds new fields to the SalesOrderShipment model

v50 -> 2022-05-18 : https://github.com/inventree/InvenTree/pull/2912
    - Implement Attachments for manufacturer parts

v49 -> 2022-05-09 : https://github.com/inventree/InvenTree/pull/2957
    - Allows filtering of plugin list by 'active' status
    - Allows filtering of plugin list by 'mixin' support
    - Adds endpoint to "identify" or "locate" stock items and locations (using plugins)

v48 -> 2022-05-12 : https://github.com/inventree/InvenTree/pull/2977
    - Adds "export to file" functionality for PurchaseOrder API endpoint
    - Adds "export to file" functionality for SalesOrder API endpoint
    - Adds "export to file" functionality for BuildOrder API endpoint

v47 -> 2022-05-10 : https://github.com/inventree/InvenTree/pull/2964
    - Fixes barcode API error response when scanning a StockItem which does not exist
    - Fixes barcode API error response when scanning a StockLocation which does not exist

v46 -> 2022-05-09
    - Fixes read permissions on settings API
    - Allows non-staff users to read global settings via the API

v45 -> 2022-05-08 : https://github.com/inventree/InvenTree/pull/2944
    - Settings are now accessed via the API using their unique key, not their PK
    - This allows the settings to be accessed without prior knowledge of the PK

v44 -> 2022-05-04 : https://github.com/inventree/InvenTree/pull/2931
    - Converting more server-side rendered forms to the API
    - Exposes more core functionality to API endpoints

v43 -> 2022-04-26 : https://github.com/inventree/InvenTree/pull/2875
    - Adds API detail endpoint for PartSalePrice model
    - Adds API detail endpoint for PartInternalPrice model

v42 -> 2022-04-26 : https://github.com/inventree/InvenTree/pull/2833
    - Adds variant stock information to the Part and BomItem serializers

v41 -> 2022-04-26
    - Fixes 'variant_of' filter for Part list endpoint

v40 -> 2022-04-19
    - Adds ability to filter StockItem list by "tracked" parameter
        - This checks the serial number or batch code fields

v39 -> 2022-04-18
    - Adds ability to filter StockItem list by "has_batch" parameter

v38 -> 2022-04-14 : https://github.com/inventree/InvenTree/pull/2828
    - Adds the ability to include stock test results for "installed items"

v37 -> 2022-04-07 : https://github.com/inventree/InvenTree/pull/2806
    - Adds extra stock availability information to the BomItem serializer

v36 -> 2022-04-03
    - Adds ability to filter part list endpoint by unallocated_stock argument

v35 -> 2022-04-01 : https://github.com/inventree/InvenTree/pull/2797
    - Adds stock allocation information to the Part API
    - Adds calculated field for "unallocated_quantity"

v34 -> 2022-03-25
    - Change permissions for "plugin list" API endpoint (now allows any authenticated user)

v33 -> 2022-03-24
    - Adds "plugins_enabled" information to root API endpoint

v32 -> 2022-03-19
    - Adds "parameters" detail to Part API endpoint (use &parameters=true)
    - Adds ability to filter PartParameterTemplate API by Part instance
    - Adds ability to filter PartParameterTemplate API by PartCategory instance

v31 -> 2022-03-14
    - Adds "updated" field to SupplierPriceBreakList and SupplierPriceBreakDetail API endpoints

v30 -> 2022-03-09
    - Adds "exclude_location" field to BuildAutoAllocation API endpoint
    - Allows BuildItem API endpoint to be filtered by BomItem relation

v29 -> 2022-03-08
    - Adds "scheduling" endpoint for predicted stock scheduling information

v28 -> 2022-03-04
    - Adds an API endpoint for auto allocation of stock items against a build order
    - Ref: https://github.com/inventree/InvenTree/pull/2713

v27 -> 2022-02-28
    - Adds target_date field to individual line items for purchase orders and sales orders

v26 -> 2022-02-17
    - Adds API endpoint for uploading a BOM file and extracting data

v25 -> 2022-02-17
    - Adds ability to filter "part" list endpoint by "in_bom_for" argument

v24 -> 2022-02-10
    - Adds API endpoint for deleting (cancelling) build order outputs

v23 -> 2022-02-02
    - Adds API endpoints for managing plugin classes
    - Adds API endpoints for managing plugin settings

v22 -> 2021-12-20
    - Adds API endpoint to "merge" multiple stock items

v21 -> 2021-12-04
    - Adds support for multiple "Shipments" against a SalesOrder
    - Refactors process for stock allocation against a SalesOrder

v20 -> 2021-12-03
    - Adds ability to filter POLineItem endpoint by "base_part"
    - Adds optional "order_detail" to POLineItem list endpoint

v19 -> 2021-12-02
    - Adds the ability to filter the StockItem API by "part_tree"
    - Returns only stock items which match a particular part.tree_id field

v18 -> 2021-11-15
    - Adds the ability to filter BomItem API by "uses" field
    - This returns a list of all BomItems which "use" the specified part
    - Includes inherited BomItem objects

v17 -> 2021-11-09
    - Adds API endpoints for GLOBAL and USER settings objects
    - Ref: https://github.com/inventree/InvenTree/pull/2275

v16 -> 2021-10-17
    - Adds API endpoint for completing build order outputs

v15 -> 2021-10-06
    - Adds detail endpoint for SalesOrderAllocation model
    - Allows use of the API forms interface for adjusting SalesOrderAllocation objects

v14 -> 2021-10-05
    - Stock adjustment actions API is improved, using native DRF serializer support
    - However adjustment actions now only support 'pk' as a lookup field

v13 -> 2021-10-05
    - Adds API endpoint to allocate stock items against a BuildOrder
    - Updates StockItem API with improved filtering against BomItem data

v12 -> 2021-09-07
    - Adds API endpoint to receive stock items against a PurchaseOrder

v11 -> 2021-08-26
    - Adds "units" field to PartBriefSerializer
    - This allows units to be introspected from the "part_detail" field in the StockItem serializer

v10 -> 2021-08-23
    - Adds "purchase_price_currency" to StockItem serializer
    - Adds "purchase_price_string" to StockItem serializer
    - Purchase price is now writable for StockItem serializer

v9  -> 2021-08-09
    - Adds "price_string" to part pricing serializers

v8  -> 2021-07-19
    - Refactors the API interface for SupplierPart and ManufacturerPart models
    - ManufacturerPart objects can no longer be created via the SupplierPart API endpoint

v7  -> 2021-07-03
    - Introduced the concept of "API forms" in https://github.com/inventree/InvenTree/pull/1716
    - API OPTIONS endpoints provide comprehensive field metedata
    - Multiple new API endpoints added for database models

v6  -> 2021-06-23
    - Part and Company images can now be directly uploaded via the REST API

v5  -> 2021-06-21
    - Adds API interface for manufacturer part parameters

v4  -> 2021-06-01
    - BOM items can now accept "variant stock" to be assigned against them
    - Many slight API tweaks were needed to get this to work properly!

v3  -> 2021-05-22:
    - The updated StockItem "history tracking" now uses a different interface

"""
