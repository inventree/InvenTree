"""InvenTree API version information."""

# InvenTree API version
INVENTREE_API_VERSION = 342

"""Increment this API version number whenever there is a significant change to the API that any clients need to know about."""


INVENTREE_API_TEXT = """
v342 -> 2025-05-09 : https://github.com/inventree/InvenTree/pull/9651
    - Fix serializer to match Generate API for serial numbers

v341 -> 2025-04-21 : https://github.com/inventree/InvenTree/pull/9547
    - Require pagination limit on list queries

v340 -> 2025-04-15 : https://github.com/inventree/InvenTree/pull/9546
    - Add nullable to various fields to make them not required

v339 -> 2025-04-15 : https://github.com/inventree/InvenTree/pull/9283
    - Remove need for source in /plugins/ui/features

v338 -> 2025-04-15 : https://github.com/inventree/InvenTree/pull/9333
    - Adds oAuth2 support for the API

v337 -> 2025-04-15 : https://github.com/inventree/InvenTree/pull/9505
    - Adds API endpoint with extra serial number information for a given StockItem object

v336 -> 2025-04-10 : https://github.com/inventree/InvenTree/pull/9492
    - Fixed query and response serialization for units_all and version_text
    - Fixed LicenseView and VersionInformation serialization

v335 -> 2025-04-09 : https://github.com/inventree/InvenTree/pull/9476
    - Adds "roles" detail to the Group API endpoint
    - Adds "users" detail to the Group API endpoint
    - Adds "groups" detail to the User API endpoint

v334 -> 2025-04-08 : https://github.com/inventree/InvenTree/pull/9453
    - Fixes various operationId and enum collisions and help texts

v333 -> 2025-04-03 : https://github.com/inventree/InvenTree/pull/9452
    - Currency string is no longer restricted to a hardcoded enum
    - Customizable status keys are no longer hardcoded enum values

v332 -> 2025-04-02 : https://github.com/inventree/InvenTree/pull/9393
    - Adds 'search_notes' parameter to all searchable API endpoints

v331 -> 2025-04-01 : https://github.com/inventree/InvenTree/pull/9437
    - Set correct types on various formerly-string PK fields as well permissions
    - Include metadata request and response types

v330 -> 2025-03-31 : https://github.com/inventree/InvenTree/pull/9420
    - Deconflict operation id between single and bulk destroy operations
    - Add request body definition for bulk destroy operations

v329 -> 2025-03-30 : https://github.com/inventree/InvenTree/pull/9399
    - Convert url path regex-specified PKs to int

v328 -> 2025-03-29 : https://github.com/inventree/InvenTree/pull/9407
    - Updates schema to include paging arguments

v327 -> 2025-03-20 : https://github.com/inventree/InvenTree/pull/9339
    - Adds "is_mandatory" field to the Plugin API
    - Adds ability to filter by "mandatory" status in the Plugin API

v326 -> 2025-03-18 : https://github.com/inventree/InvenTree/pull/9096
    - Overhaul the data-export API functionality
    - Allow customization of data exporting via plugins
    - Consolidate LabelOutput and ReportOutput API endpoints into single DataOutput endpoint

v325 -> 2024-03-17 : https://github.com/inventree/InvenTree/pull/9244
    - Adds the option for superusers to list all user tokens
    - Make list endpoints sortable, filterable and searchable

v324 -> 2025-03-17 : https://github.com/inventree/InvenTree/pull/9320
    - Adds BulkUpdate support for the SalesOrderAllocation model
    - Adds BulkUpdate support for the PartCategory model
    - Adds BulkUpdate support for the StockLocation model

v323 -> 2025-03-17 : https://github.com/inventree/InvenTree/pull/9313
    - Adds BulkUpdate support to the Part API endpoint
    - Remove legacy API endpoint to set part category for multiple parts

v322 -> 2025-03-16 : https://github.com/inventree/InvenTree/pull/8933
    - Add min_date and max_date query filters for orders, for use in calendar views

v321 -> 2025-03-06 : https://github.com/inventree/InvenTree/pull/9236
    - Adds conditionally-returned fields to the schema to match API behavior
    - Removes required flag for nullable read-only fields to match API behavior

v320 -> 2025-03-05 : https://github.com/inventree/InvenTree/pull/9243
    - Link fields are now up to 2000 chars long

v319 -> 2025-03-04 : https://github.com/inventree/InvenTree/pull/9199
    - Add detail API endpoint for the LabelOutput model
    - Add detail API endpoint for the ReportOutput model

v318 -> 2025-02-25 : https://github.com/inventree/InvenTree/pull/9116
    - Adds user profile API endpoints

v317 -> 2025-02-26 : https://github.com/inventree/InvenTree/pull/9143
    - Default 'overdue' field to False in Build serializer
    - Add allow_null to various fields in Build, Settings, Order, Part, and Stock serializers
    - Add type hints to Users model to properly type fields

v316 -> 2025-02-26 : https://github.com/inventree/InvenTree/pull/9185
    - Allow 'icon' field to be nullified in the PartCategory API
    - Allow 'custom_icon' field to be nullified in the StockLocation API

v315 -> 2025-02-22 : https://github.com/inventree/InvenTree/pull/9150
    - Remove outdated 'url' field from some API endpoints

v314 -> 2025-02-17 : https://github.com/inventree/InvenTree/pull/6293
    - Removes a considerable amount of old auth endpoints
    - Introduces allauth-provided auth endpoints

v313 -> 2025-02-17 : https://github.com/inventree/InvenTree/pull/9087
    - Adds instance id optionally to the info view endpoint

v312 -> 2025-02-15 : https://github.com/inventree/InvenTree/pull/9079
    - Remove old API endpoints associated with legacy BOM import functionality

v311 -> 2025-02-14 : https://github.com/inventree/InvenTree/pull/9076
    - Adds "model_filters" attribute to settings API

v310 -> 2025-02-14 : https://github.com/inventree/InvenTree/pull/9077
    - Adds 'is_variant' filter to the Part list API

v309 -> 2025-02-02 : https://github.com/inventree/InvenTree/pull/9008
    - Bug fixes for the "Part" serializer
    - Fixes for data import API endpoints

v308 -> 2025-02-01 : https://github.com/inventree/InvenTree/pull/9003
    - Adds extra detail to the ReportOutput and LabelOutput API endpoints
    - Allows ordering of output list endpoints

v307 -> 2025-01-29 : https://github.com/inventree/InvenTree/pull/8969
    - Extend Info Endpoint to include customizations

v306 -> 2025-01-28 : https://github.com/inventree/InvenTree/pull/8966
    - Adds "start_date" to PurchasesOrder API
    - Adds "start_date" to SalesOrder API
    - Adds "start_date" to ReturnOrder API
    - Updated API filters

v305 -> 2025-01-26 : https://github.com/inventree/InvenTree/pull/8950
    - Bug fixes for the SupplierPart API
    - Refactoring for data export via API

v304 -> 2025-01-22 : https://github.com/inventree/InvenTree/pull/8940
    - Adds "category" filter to build list API

v303 -> 2025-01-20 : https://github.com/inventree/InvenTree/pull/8915
    - Adds "start_date" field to Build model and API endpoints
    - Adds additional API filtering and sorting options for Build list

v302 -> 2025-01-18 : https://github.com/inventree/InvenTree/pull/8905
    - Fix schema definition on the /label/print endpoint

v301 -> 2025-01-14 : https://github.com/inventree/InvenTree/pull/8894
    - Remove ui preferences from the API

v300 -> 2025-01-13 : https://github.com/inventree/InvenTree/pull/8886
    - Allow null value for 'expiry_date' field introduced in #8867

v299 -> 2025-01-10 : https://github.com/inventree/InvenTree/pull/8867
    - Adds 'expiry_date' field to the PurchaseOrderReceive API endpoint
    - Adds 'default_expiry` field to the PartBriefSerializer, affecting API endpoints which use it

v298 -> 2025-01-07 : https://github.com/inventree/InvenTree/pull/8848
    - Adds 'created_by' field to PurchaseOrder API endpoints
    - Adds 'created_by' field to SalesOrder API endpoints
    - Adds 'created_by' field to ReturnOrder API endpoints

v297 -> 2024-12-29 : https://github.com/inventree/InvenTree/pull/8438
    - Adjustments to the CustomUserState API endpoints and serializers

v296 -> 2024-12-25 : https://github.com/inventree/InvenTree/pull/8732
    - Adjust default "part_detail" behavior for StockItem API endpoints

v295 -> 2024-12-23 : https://github.com/inventree/InvenTree/pull/8746
    - Improve API documentation for build APIs

v294 -> 2024-12-23 : https://github.com/inventree/InvenTree/pull/8738
    - Extends registration API documentation

v293 -> 2024-12-14 : https://github.com/inventree/InvenTree/pull/8658
    - Adds new fields to the supplier barcode API endpoints

v292 -> 2024-12-03 : https://github.com/inventree/InvenTree/pull/8625
    - Add "on_order" and "in_stock" annotations to SupplierPart API
    - Enhanced filtering for the SupplierPart API

v291 -> 2024-11-30 : https://github.com/inventree/InvenTree/pull/8596
    - Allow null / empty values for plugin settings

v290 -> 2024-11-29 : https://github.com/inventree/InvenTree/pull/8590
    - Adds "quantity" field to ReturnOrderLineItem model and API

v289 -> 2024-11-27 : https://github.com/inventree/InvenTree/pull/8570
    - Enable status change when transferring stock items

v288 -> 2024-11-27 : https://github.com/inventree/InvenTree/pull/8574
    - Adds "consumed" filter to StockItem API

v287 -> 2024-11-27 : https://github.com/inventree/InvenTree/pull/8571
    - Adds ability to set stock status when returning items from a customer

v286 -> 2024-11-26 : https://github.com/inventree/InvenTree/pull/8054
    - Adds "SelectionList" and "SelectionListEntry" API endpoints

v285 -> 2024-11-25 : https://github.com/inventree/InvenTree/pull/8559
    - Adds better description for registration endpoints

v284 -> 2024-11-25 : https://github.com/inventree/InvenTree/pull/8544
    - Adds new date filters to the StockItem API
    - Adds new date filters to the BuildOrder API
    - Adds new date filters to the SalesOrder API
    - Adds new date filters to the PurchaseOrder API
    - Adds new date filters to the ReturnOrder API

v283 -> 2024-11-20 : https://github.com/inventree/InvenTree/pull/8524
    - Adds "note" field to the PartRelated API endpoint

v282 -> 2024-11-19 : https://github.com/inventree/InvenTree/pull/8487
    - Remove the "test statistics" API endpoints
    - This is now provided via a custom plugin

v281 -> 2024-11-15 : https://github.com/inventree/InvenTree/pull/8480
    - Fixes StockHistory API data serialization

v280 -> 2024-11-10 : https://github.com/inventree/InvenTree/pull/8461
    - Makes schema for API information endpoint more informing
    - Removes general not found endpoint

v279 -> 2024-11-09 : https://github.com/inventree/InvenTree/pull/8458
    - Adds "order_outstanding" and "part" filters to the BuildLine API endpoint
    - Adds "order_outstanding" filter to the SalesOrderLineItem API endpoint

v278 -> 2024-11-07 : https://github.com/inventree/InvenTree/pull/8445
    - Updates to the SalesOrder API endpoints
    - Add "shipment count" information to the SalesOrder API endpoints
    - Allow null value for SalesOrderAllocation.shipment field
    - Additional filtering options for allocation endpoints

v277 -> 2024-11-01 : https://github.com/inventree/InvenTree/pull/8278
    - Allow build order list to be filtered by "outstanding" (alias for "active")

v276 -> 2024-10-31 : https://github.com/inventree/InvenTree/pull/8403
    - Adds 'destination' field to the PurchaseOrder model and API endpoints

v275 -> 2024-10-31 : https://github.com/inventree/InvenTree/pull/8396
    - Adds SKU and MPN fields to the StockItem serializer
    - Additional export options for the StockItem serializer

v274 -> 2024-10-29 : https://github.com/inventree/InvenTree/pull/8392
    - Add more detailed information to NotificationEntry API serializer

v273 -> 2024-10-28 : https://github.com/inventree/InvenTree/pull/8376
    - Fixes for the BuildLine API endpoint

v272 -> 2024-10-25 : https://github.com/inventree/InvenTree/pull/8343
    - Adjustments to BuildLine API serializers

v271 -> 2024-10-22 : https://github.com/inventree/InvenTree/pull/8331
    - Fixes for SalesOrderLineItem endpoints

v270 -> 2024-10-19 : https://github.com/inventree/InvenTree/pull/8307
    - Adds missing date fields from order API endpoint(s)

v269 -> 2024-10-16 : https://github.com/inventree/InvenTree/pull/8295
    - Adds "include_variants" filter to the BuildOrder API endpoint
    - Adds "include_variants" filter to the SalesOrder API endpoint
    - Adds "include_variants" filter to the PurchaseOrderLineItem API endpoint
    - Adds "include_variants" filter to the ReturnOrder API endpoint

v268 -> 2024-10-11 : https://github.com/inventree/InvenTree/pull/8274
    - Adds "in_stock" attribute to the StockItem serializer

v267 -> 2024-10-8 : https://github.com/inventree/InvenTree/pull/8250
    - Remove "allocations" field from the SalesOrderShipment API endpoint(s)
    - Add "allocated_items" field to the SalesOrderShipment API endpoint(s)

v266 -> 2024-10-07 : https://github.com/inventree/InvenTree/pull/8249
    - Tweak SalesOrderShipment API for more efficient data retrieval

v265 -> 2024-10-07 : https://github.com/inventree/InvenTree/pull/8228
    - Adds API endpoint for providing custom admin integration details for plugins

v264 -> 2024-10-03 : https://github.com/inventree/InvenTree/pull/8231
    - Adds Sales Order Shipment attachment model type

v263 -> 2024-09-30 : https://github.com/inventree/InvenTree/pull/8194
    - Adds Sales Order Shipment report

v262 -> 2024-09-30 : https://github.com/inventree/InvenTree/pull/8220
    - Tweak permission requirements for uninstalling plugins via API

v261 -> 2024-09-26 : https://github.com/inventree/InvenTree/pull/8184
    - Fixes for BuildOrder API serializers

v260 -> 2024-09-26 : https://github.com/inventree/InvenTree/pull/8190
    - Adds facility for server-side context data to be passed to client-side plugins

v259 -> 2024-09-20 : https://github.com/inventree/InvenTree/pull/8137
    - Implements new API endpoint for enabling custom UI features via plugins

v258 -> 2024-09-24 : https://github.com/inventree/InvenTree/pull/8163
    - Enhances the existing PartScheduling API endpoint
    - Adds a formal DRF serializer to the endpoint

v257 -> 2024-09-22 : https://github.com/inventree/InvenTree/pull/8150
    - Adds API endpoint for reporting barcode scan history

v256 -> 2024-09-19 : https://github.com/inventree/InvenTree/pull/7704
    - Adjustments for "stocktake" (stock history) API endpoints

v255 -> 2024-09-19 : https://github.com/inventree/InvenTree/pull/8145
    - Enables copying line items when duplicating an order

v254 -> 2024-09-14 : https://github.com/inventree/InvenTree/pull/7470
    - Implements new API endpoints for enabling custom UI functionality via plugins

v253 -> 2024-09-14 : https://github.com/inventree/InvenTree/pull/7944
    - Adjustments for user API endpoints

v252 -> 2024-09-13 : https://github.com/inventree/InvenTree/pull/8040
    - Add endpoint for listing all known units

v251 -> 2024-09-06 : https://github.com/inventree/InvenTree/pull/8018
    - Adds "attach_to_model" field to the ReportTemplate model

v250 -> 2024-09-04 : https://github.com/inventree/InvenTree/pull/8069
    - Fixes 'revision' field definition in Part serializer

v249 -> 2024-08-23 : https://github.com/inventree/InvenTree/pull/7978
    - Sort status enums

v248 -> 2024-08-23 : https://github.com/inventree/InvenTree/pull/7965
    - Small adjustments to labels for new custom status fields

v247 -> 2024-08-22 : https://github.com/inventree/InvenTree/pull/7956
    - Adjust "attachment" field on StockItemTestResult serializer
    - Allow null values for attachment

v246 -> 2024-08-21 : https://github.com/inventree/InvenTree/pull/7862
    - Adds custom status fields to various serializers
    - Adds endpoints to admin custom status fields

v245 -> 2024-08-21 : https://github.com/inventree/InvenTree/pull/7520
    - Documented pagination fields (no functional changes)

v244 -> 2024-08-21 : https://github.com/inventree/InvenTree/pull/7941
    - Adds "create_child_builds" field to the Build API
    - Write-only field to create child builds from the API
    - Only available when creating a new build order

v243 -> 2024-08-21 : https://github.com/inventree/InvenTree/pull/7940
    - Expose "ancestor" filter to the BuildOrder API

v242 -> 2024-08-20 : https://github.com/inventree/InvenTree/pull/7932
    - Adds "level" attribute to BuildOrder serializer
    - Allow ordering of BuildOrder API by "level" attribute
    - Allow "parent" filter for BuildOrder API to have "cascade=True" option

v241 -> 2024-08-18 : https://github.com/inventree/InvenTree/pull/7906
    - Adjusts required fields for the MeUserDetail endpoint

v240 -> 2024-08-16 : https://github.com/inventree/InvenTree/pull/7900
    - Adjust "issued_by" filter for the BuildOrder list endpoint
    - Adjust "assigned_to" filter for the BuildOrder list endpoint

v239 -> 2024-08-15 : https://github.com/inventree/InvenTree/pull/7888
    - Adds "testable" field to the Part model
    - Adds associated filters to various API endpoints

v238 -> 2024-08-14 : https://github.com/inventree/InvenTree/pull/7874
    - Add "assembly" filter to BuildLine API endpoint

v237 -> 2024-08-13 : https://github.com/inventree/InvenTree/pull/7863
    - Reimplement "bulk delete" operation for Attachment model
    - Fix permission checks for Attachment API endpoints

v236 -> 2024-08-10 : https://github.com/inventree/InvenTree/pull/7844
    - Adds "supplier_name" to the PurchaseOrder API serializer

v235 -> 2024-08-08 : https://github.com/inventree/InvenTree/pull/7837
    - Adds "on_order" quantity to SalesOrderLineItem serializer
    - Adds "building" quantity to SalesOrderLineItem serializer

v234 -> 2024-08-08 : https://github.com/inventree/InvenTree/pull/7829
    - Fixes bug in the plugin metadata endpoint

v233 -> 2024-08-04 : https://github.com/inventree/InvenTree/pull/7807
    - Adds new endpoints for managing state of build orders
    - Adds new endpoints for managing state of purchase orders
    - Adds new endpoints for managing state of sales orders
    - Adds new endpoints for managing state of return orders

v232 -> 2024-08-03 : https://github.com/inventree/InvenTree/pull/7793
    - Allow ordering of SalesOrderShipment API by 'shipment_date' and 'delivery_date'

v231 -> 2024-08-03 : https://github.com/inventree/InvenTree/pull/7794
    - Optimize BuildItem and BuildLine serializers to improve API efficiency

v230 -> 2024-05-05 : https://github.com/inventree/InvenTree/pull/7164
    - Adds test statistics endpoint

v229 -> 2024-07-31 : https://github.com/inventree/InvenTree/pull/7775
    - Add extra exportable fields to the BomItem serializer

v228 -> 2024-07-18 : https://github.com/inventree/InvenTree/pull/7684
    - Adds "icon" field to the PartCategory.path and StockLocation.path API
    - Adds icon packages API endpoint

v227 -> 2024-07-19 : https://github.com/inventree/InvenTree/pull/7693/
    - Adds endpoints to list and revoke the tokens issued to the current user

v226 -> 2024-07-15 : https://github.com/inventree/InvenTree/pull/7648
    - Adds barcode generation API endpoint

v225 -> 2024-07-17 : https://github.com/inventree/InvenTree/pull/7671
    - Adds "filters" field to DataImportSession API

v224 -> 2024-07-14 : https://github.com/inventree/InvenTree/pull/7667
    - Add notes field to ManufacturerPart and SupplierPart API endpoints

v223 -> 2024-07-14 : https://github.com/inventree/InvenTree/pull/7649
    - Allow adjustment of "packaging" field when receiving items against a purchase order

v222 -> 2024-07-14 : https://github.com/inventree/InvenTree/pull/7635
    - Adjust the BomItem API endpoint to improve data import process

v221 -> 2024-07-13 : https://github.com/inventree/InvenTree/pull/7636
    - Adds missing fields from StockItemBriefSerializer
    - Adds missing fields from PartBriefSerializer
    - Adds extra exportable fields to BuildItemSerializer

v220 -> 2024-07-11 : https://github.com/inventree/InvenTree/pull/7585
    - Adds "revision_of" field to Part serializer
    - Adds new API filters for "revision" status

v219 -> 2024-07-11 : https://github.com/inventree/InvenTree/pull/7611
    - Adds new fields to the BuildItem API endpoints
    - Adds new ordering / filtering options to the BuildItem API endpoints

v218 -> 2024-07-11 : https://github.com/inventree/InvenTree/pull/7619
    - Adds "can_build" field to the BomItem API

v217 -> 2024-07-09 : https://github.com/inventree/InvenTree/pull/7599
    - Fixes bug in "project_code" field for order API endpoints

v216 -> 2024-07-08 : https://github.com/inventree/InvenTree/pull/7595
    - Moves API endpoint for contenttype lookup by model name

v215 -> 2024-07-09 : https://github.com/inventree/InvenTree/pull/7591
    - Adds additional fields to the BuildLine serializer

v214 -> 2024-07-08 : https://github.com/inventree/InvenTree/pull/7587
    - Adds "default_location_detail" field to the Part API

v213 -> 2024-07-06 : https://github.com/inventree/InvenTree/pull/7527
    - Adds 'locked' field to Part API

v212 -> 2024-07-06 : https://github.com/inventree/InvenTree/pull/7562
    - Makes API generation more robust (no functional changes)

v211 -> 2024-06-26 : https://github.com/inventree/InvenTree/pull/6911
    - Adds API endpoints for managing data import and export

v210 -> 2024-06-26 : https://github.com/inventree/InvenTree/pull/7518
    - Adds translatable text to User API fields

v209 -> 2024-06-26 : https://github.com/inventree/InvenTree/pull/7514
    - Add "top_level" filter to PartCategory API endpoint
    - Add "top_level" filter to StockLocation API endpoint

v208 -> 2024-06-19 : https://github.com/inventree/InvenTree/pull/7479
    - Adds documentation for the user roles API endpoint (no functional changes)

v207 -> 2024-06-09 : https://github.com/inventree/InvenTree/pull/7420
    - Moves all "Attachment" models into a single table
    - All "Attachment" operations are now performed at /api/attachment/
    - Add permissions information to /api/user/roles/ endpoint

v206 -> 2024-06-08 : https://github.com/inventree/InvenTree/pull/7417
    - Adds "choices" field to the PartTestTemplate model

v205 -> 2024-06-03 : https://github.com/inventree/InvenTree/pull/7284
    - Added model_type and model_id fields to the "NotesImage" serializer

v204 -> 2024-06-03 : https://github.com/inventree/InvenTree/pull/7393
    - Fixes previous API update which resulted in inconsistent ordering of currency codes

v203 -> 2024-06-03 : https://github.com/inventree/InvenTree/pull/7390
    - Currency codes are now configurable as a run-time setting

v202 -> 2024-05-27 : https://github.com/inventree/InvenTree/pull/7343
    - Adjust "required" attribute of Part.category field to be optional

v201 -> 2024-05-21 : https://github.com/inventree/InvenTree/pull/7074
    - Major refactor of the report template / report printing interface
    - This is a *breaking change* to the report template API

v200 -> 2024-05-20 : https://github.com/inventree/InvenTree/pull/7000
    - Adds API endpoint for generating custom batch codes
    - Adds API endpoint for generating custom serial numbers

v199 -> 2024-05-20 : https://github.com/inventree/InvenTree/pull/7264
    - Expose "bom_valid" filter for the Part API
    - Expose "starred" filter for the Part API

v198 -> 2024-05-19 : https://github.com/inventree/InvenTree/pull/7258
    - Fixed lookup field conflicts in the plugins API

v197 -> 2024-05-14 : https://github.com/inventree/InvenTree/pull/7224
    - Refactor the plugin API endpoints to use the plugin "key" for lookup, rather than the PK value

v196 -> 2024-05-05 : https://github.com/inventree/InvenTree/pull/7160
    - Adds "location" field to BuildOutputComplete API endpoint

v195 -> 2024-05-03 : https://github.com/inventree/InvenTree/pull/7153
    - Fixes bug in BuildOrderCancel API endpoint

v194 -> 2024-05-01 : https://github.com/inventree/InvenTree/pull/7147
    -  Adds field description to the currency_exchange_retrieve API call

v193 -> 2024-04-30 : https://github.com/inventree/InvenTree/pull/7144
    - Adds "assigned_to" filter to PurchaseOrder / SalesOrder / ReturnOrder API endpoints

v192 -> 2024-04-23 : https://github.com/inventree/InvenTree/pull/7106
    - Adds 'trackable' ordering option to BuildLineLabel API endpoint

v191 -> 2024-04-22 : https://github.com/inventree/InvenTree/pull/7079
    - Adds API endpoints for Contenttype model

v190 -> 2024-04-19 : https://github.com/inventree/InvenTree/pull/7024
    - Adds "active" field to the Company API endpoints
    - Allow company list to be filtered by "active" status

v189 -> 2024-04-19 : https://github.com/inventree/InvenTree/pull/7066
    - Adds "currency" field to CompanyBriefSerializer class

v188 -> 2024-04-16 : https://github.com/inventree/InvenTree/pull/6970
    - Adds session authentication support for the API
    - Improvements for login / logout endpoints for better support of React web interface

v187 -> 2024-04-10 : https://github.com/inventree/InvenTree/pull/6985
    - Allow Part list endpoint to be sorted by pricing_min and pricing_max values
    - Allow BomItem list endpoint to be sorted by pricing_min and pricing_max values
    - Allow InternalPrice and SalePrice endpoints to be sorted by quantity
    - Adds total pricing values to BomItem serializer

v186 -> 2024-03-26 : https://github.com/inventree/InvenTree/pull/6855
    - Adds license information to the API

v185 -> 2024-03-24 : https://github.com/inventree/InvenTree/pull/6836
    - Remove /plugin/activate endpoint
    - Update docstrings and typing for various API endpoints (no functional changes)

v184 -> 2024-03-17 : https://github.com/inventree/InvenTree/pull/10464
    - Add additional fields for tests (start/end datetime, test station)

v183 -> 2024-03-14 : https://github.com/inventree/InvenTree/pull/5972
    - Adds "category_default_location" annotated field to part serializer
    - Adds "part_detail.category_default_location" annotated field to stock item serializer
    - Adds "part_detail.category_default_location" annotated field to purchase order line serializer
    - Adds "parent_default_location" annotated field to category serializer

v182 -> 2024-03-13 : https://github.com/inventree/InvenTree/pull/6714
    - Expose ReportSnippet model to the /report/snippet/ API endpoint
    - Expose ReportAsset model to the /report/asset/ API endpoint

v181 -> 2024-02-21 : https://github.com/inventree/InvenTree/pull/6541
    - Adds "width" and "height" fields to the LabelTemplate API endpoint
    - Adds "page_size" and "landscape" fields to the ReportTemplate API endpoint

v180 -> 2024-3-02 : https://github.com/inventree/InvenTree/pull/6463
    - Tweaks to API documentation to allow automatic documentation generation

v179 -> 2024-03-01 : https://github.com/inventree/InvenTree/pull/6605
    - Adds "subcategories" count to PartCategory serializer
    - Adds "sublocations" count to StockLocation serializer
    - Adds "image" field to PartBrief serializer
    - Adds "image" field to CompanyBrief serializer

v178 -> 2024-02-29 : https://github.com/inventree/InvenTree/pull/6604
    - Adds "external_stock" field to the Part API endpoint
    - Adds "external_stock" field to the BomItem API endpoint
    - Adds "external_stock" field to the BuildLine API endpoint
    - Stock quantities represented in the BuildLine API endpoint are now filtered by Build.source_location

v177 -> 2024-02-27 : https://github.com/inventree/InvenTree/pull/6581
    - Adds "subcategories" count to PartCategoryTree serializer
    - Adds "sublocations" count to StockLocationTree serializer

v176 -> 2024-02-26 : https://github.com/inventree/InvenTree/pull/6535
    - Adds the field "plugins_install_disabled" to the Server info API endpoint

v175 -> 2024-02-21 : https://github.com/inventree/InvenTree/pull/6538
    - Adds "parts" count to PartParameterTemplate serializer

v174 -> 2024-02-21 : https://github.com/inventree/InvenTree/pull/6536
    - Expose PartCategory filters to the API documentation
    - Expose StockLocation filters to the API documentation

v173 -> 2024-02-20 : https://github.com/inventree/InvenTree/pull/6483
    - Adds "merge_items" to the PurchaseOrderLine create API endpoint
    - Adds "auto_pricing" to the PurchaseOrderLine create/update API endpoint

v172 -> 2024-02-20 : https://github.com/inventree/InvenTree/pull/6526
    - Adds "enabled" field to the PartTestTemplate API endpoint
    - Adds "enabled" filter to the PartTestTemplate list
    - Adds "enabled" filter to the StockItemTestResult list

v171 -> 2024-02-19 : https://github.com/inventree/InvenTree/pull/6516
    - Adds "key" as a filterable parameter to PartTestTemplate list endpoint

v170 -> 2024-02-19 : https://github.com/inventree/InvenTree/pull/6514
    - Adds "has_results" filter to the PartTestTemplate list endpoint

v169 -> 2024-02-14 : https://github.com/inventree/InvenTree/pull/6430
    - Adds 'key' field to PartTestTemplate API endpoint
    - Adds annotated 'results' field to PartTestTemplate API endpoint
    - Adds 'template' field to StockItemTestResult API endpoint

v168 -> 2024-02-14 : https://github.com/inventree/InvenTree/pull/4824
    - Adds machine CRUD API endpoints
    - Adds machine settings API endpoints
    - Adds machine restart API endpoint
    - Adds machine types/drivers list API endpoints
    - Adds machine registry status API endpoint
    - Adds 'required' field to the global Settings API
    - Discover sub-sub classes of the StatusCode API

v167 -> 2024-02-07: https://github.com/inventree/InvenTree/pull/6440
    - Fixes for OpenAPI schema generation

v166 -> 2024-02-04 : https://github.com/inventree/InvenTree/pull/6400
    - Adds package_name to plugin API
    - Adds mechanism for uninstalling plugins via the API

v165 -> 2024-01-28 : https://github.com/inventree/InvenTree/pull/6040
    - Adds supplier_part.name, part.creation_user, part.required_for_sales_order

v164 -> 2024-01-24 : https://github.com/inventree/InvenTree/pull/6343
    - Adds "building" quantity to BuildLine API serializer

v163 -> 2024-01-22 : https://github.com/inventree/InvenTree/pull/6314
    - Extends API endpoint to expose auth configuration information for signin pages

v162 -> 2024-01-14 : https://github.com/inventree/InvenTree/pull/6230
    - Adds API endpoints to provide information on background tasks

v161 -> 2024-01-13 : https://github.com/inventree/InvenTree/pull/6222
    - Adds API endpoint for system error information

v160 -> 2023-12-11 : https://github.com/inventree/InvenTree/pull/6072
    - Adds API endpoint for allocating stock items against a sales order via barcode scan

v159 -> 2023-12-08 : https://github.com/inventree/InvenTree/pull/6056
    - Adds API endpoint for reloading plugin registry

v158 -> 2023-11-21 : https://github.com/inventree/InvenTree/pull/5953
    - Adds API endpoint for listing all settings of a particular plugin
    - Adds API endpoint for registry status (errors)

v157 -> 2023-12-02 : https://github.com/inventree/InvenTree/pull/6021
    - Add write-only "existing_image" field to Part API serializer

v156 -> 2023-11-26 : https://github.com/inventree/InvenTree/pull/5982
    - Add POST endpoint for report and label creation

v155 -> 2023-11-24 : https://github.com/inventree/InvenTree/pull/5979
    - Add "creation_date" field to Part instance serializer

v154 -> 2023-11-21 : https://github.com/inventree/InvenTree/pull/5944
    - Adds "responsible" field to the ProjectCode table

v153 -> 2023-11-21 : https://github.com/inventree/InvenTree/pull/5956
    - Adds override_min and override_max fields to part pricing API

v152 -> 2023-11-20 : https://github.com/inventree/InvenTree/pull/5949
    - Adds barcode support for ManufacturerPart model
    - Adds API endpoint for adding parts to purchase order using barcode scan

v151 -> 2023-11-13 : https://github.com/inventree/InvenTree/pull/5906
    - Allow user list API to be filtered by user active status
    - Allow owner list API to be filtered by user active status

v150 -> 2023-11-07: https://github.com/inventree/InvenTree/pull/5875
    - Extended user API endpoints to enable ordering
    - Extended user API endpoints to enable user role changes
    - Added endpoint to create a new user

v149 -> 2023-11-07 : https://github.com/inventree/InvenTree/pull/5876
    - Add 'building' quantity to BomItem serializer
    - Add extra ordering options for the BomItem list API

v148 -> 2023-11-06 : https://github.com/inventree/InvenTree/pull/5872
    - Allow "quantity" to be specified when installing an item into another item

v147 -> 2023-11-04: https://github.com/inventree/InvenTree/pull/5860
    - Adds "completed_lines" field to SalesOrder API endpoint
    - Adds "completed_lines" field to PurchaseOrder API endpoint

v146 -> 2023-11-02: https://github.com/inventree/InvenTree/pull/5822
    - Extended SSO Provider endpoint to contain if a provider is configured
    - Adds API endpoints for Email Address model

v145 -> 2023-10-30: https://github.com/inventree/InvenTree/pull/5786
    - Allow printing labels via POST including printing options in the body

v144 -> 2023-10-23: https://github.com/inventree/InvenTree/pull/5811
    - Adds version information API endpoint

v143 -> 2023-10-29: https://github.com/inventree/InvenTree/pull/5810
    - Extends the status endpoint to include information about system status and health

v142 -> 2023-10-20: https://github.com/inventree/InvenTree/pull/5759
    - Adds generic API endpoints for looking up status models

v141 -> 2023-10-23 : https://github.com/inventree/InvenTree/pull/5774
    - Changed 'part.responsible' from User to Owner

v140 -> 2023-10-20 : https://github.com/inventree/InvenTree/pull/5664
    - Expand API token functionality
    - Multiple API tokens can be generated per user

v139 -> 2023-10-11 : https://github.com/inventree/InvenTree/pull/5509
    - Add new BarcodePOReceive endpoint to receive line items by scanning supplier barcodes

v138 -> 2023-10-11 : https://github.com/inventree/InvenTree/pull/5679
    - Settings keys are no longer case sensitive
    - Include settings units in API serializer

v137 -> 2023-10-04 : https://github.com/inventree/InvenTree/pull/5588
    - Adds StockLocationType API endpoints
    - Adds custom_icon, location_type to StockLocation endpoint

v136 -> 2023-09-23 : https://github.com/inventree/InvenTree/pull/5595
    - Adds structural to StockLocation and PartCategory tree endpoints

v135 -> 2023-09-19 : https://github.com/inventree/InvenTree/pull/5569
    - Adds location path detail to StockLocation and StockItem API endpoints
    - Adds category path detail to PartCategory and Part API endpoints

v134 -> 2023-09-11 : https://github.com/inventree/InvenTree/pull/5525
    - Allow "Attachment" list endpoints to be searched by attachment, link and comment fields

v133 -> 2023-09-08 : https://github.com/inventree/InvenTree/pull/5518
    - Add extra optional fields which can be used for StockAdjustment endpoints

v132 -> 2023-09-07 : https://github.com/inventree/InvenTree/pull/5515
    - Add 'issued_by' filter to BuildOrder API list endpoint

v131 -> 2023-08-09 : https://github.com/inventree/InvenTree/pull/5415
    - Annotate 'available_variant_stock' to the SalesOrderLine serializer

v130 -> 2023-07-14 : https://github.com/inventree/InvenTree/pull/5251
    - Refactor label printing interface

v129 -> 2023-07-06 : https://github.com/inventree/InvenTree/pull/5189
    - Changes 'serial_lte' and 'serial_gte' stock filters to point to 'serial_int' field

v128 -> 2023-07-06 : https://github.com/inventree/InvenTree/pull/5186
    - Adds 'available' filter for BuildLine API endpoint

v127 -> 2023-06-24 : https://github.com/inventree/InvenTree/pull/5094
    - Enhancements for the PartParameter API endpoints

v126 -> 2023-06-19 : https://github.com/inventree/InvenTree/pull/5075
    - Adds API endpoint for setting the "category" for multiple parts simultaneously

v125 -> 2023-06-17 : https://github.com/inventree/InvenTree/pull/5064
    - Adds API endpoint for setting the "status" field for multiple stock items simultaneously

v124 -> 2023-06-17 : https://github.com/inventree/InvenTree/pull/5057
    - Add "created_before" and "created_after" filters to the Part API

v123 -> 2023-06-15 : https://github.com/inventree/InvenTree/pull/5019
    - Add Metadata to: Plugin Config

v122 -> 2023-06-14 : https://github.com/inventree/InvenTree/pull/5034
    - Adds new BuildLineLabel label type

v121 -> 2023-06-14 : https://github.com/inventree/InvenTree/pull/4808
    - Adds "ProjectCode" link to Build model

v120 -> 2023-06-07 : https://github.com/inventree/InvenTree/pull/4855
    - Major overhaul of the build order API
    - Adds new BuildLine model

v119 -> 2023-06-01 : https://github.com/inventree/InvenTree/pull/4898
    - Add Metadata to:  Part test templates, Part parameters, Part category parameter templates, BOM item substitute, Related Parts, Stock item test result

v118 -> 2023-06-01 : https://github.com/inventree/InvenTree/pull/4935
    - Adds extra fields for the PartParameterTemplate model

v117 -> 2023-05-22 : https://github.com/inventree/InvenTree/pull/4854
    - Part.units model now supports physical units (e.g. "kg", "m", "mm", etc)
    - Replaces SupplierPart "pack_size" field with "pack_quantity"
    - New field supports physical units, and allows for conversion between compatible units

v116 -> 2023-05-18 : https://github.com/inventree/InvenTree/pull/4823
    - Updates to part parameter implementation, to use physical units

v115 -> 2023-05-18 : https://github.com/inventree/InvenTree/pull/4846
    - Adds ability to partially scrap a build output

v114 -> 2023-05-16 : https://github.com/inventree/InvenTree/pull/4825
    - Adds "delivery_date" to shipments

v113 -> 2023-05-13 : https://github.com/inventree/InvenTree/pull/4800
    - Adds API endpoints for scrapping a build output

v112 -> 2023-05-13: https://github.com/inventree/InvenTree/pull/4741
    - Adds flag use_pack_size to the stock addition API, which allows adding packs

v111 -> 2023-05-02 : https://github.com/inventree/InvenTree/pull/4367
    - Adds tags to the Part serializer
    - Adds tags to the SupplierPart serializer
    - Adds tags to the ManufacturerPart serializer
    - Adds tags to the StockItem serializer
    - Adds tags to the StockLocation serializer

v110 -> 2023-04-26 : https://github.com/inventree/InvenTree/pull/4698
    - Adds 'order_currency' field for PurchaseOrder / SalesOrder endpoints

v109 -> 2023-04-19 : https://github.com/inventree/InvenTree/pull/4636
    - Adds API endpoints for the "ProjectCode" model

v108 -> 2023-04-17 : https://github.com/inventree/InvenTree/pull/4615
    - Adds functionality to upload images for rendering in markdown notes

v107 -> 2023-04-04 : https://github.com/inventree/InvenTree/pull/4575
    - Adds barcode support for PurchaseOrder model
    - Adds barcode support for ReturnOrder model
    - Adds barcode support for SalesOrder model
    - Adds barcode support for BuildOrder model

v106 -> 2023-04-03 : https://github.com/inventree/InvenTree/pull/4566
    - Adds 'search_regex' parameter to all searchable API endpoints

v105 -> 2023-03-31 : https://github.com/inventree/InvenTree/pull/4543
    - Adds API endpoints for status label information on various models

v104 -> 2023-03-23 : https://github.com/inventree/InvenTree/pull/4488
    - Adds various endpoints for new "ReturnOrder" models
    - Adds various endpoints for new "ReturnOrderReport" templates
    - Exposes API endpoints for "Contact" model

v103 -> 2023-03-17 : https://github.com/inventree/InvenTree/pull/4410
    - Add metadata to several more models

v102 -> 2023-03-18 : https://github.com/inventree/InvenTree/pull/4505
- Adds global search API endpoint for consolidated search results

v101 -> 2023-03-07 : https://github.com/inventree/InvenTree/pull/4462
    - Adds 'total_in_stock' to Part serializer, and supports API ordering

v100 -> 2023-03-04 : https://github.com/inventree/InvenTree/pull/4452
     - Adds bulk delete of PurchaseOrderLineItems to API

v99 -> 2023-03-03 : https://github.com/inventree/InvenTree/pull/4445
    - Adds sort by "responsible" to PurchaseOrderAPI

v98 -> 2023-02-24 : https://github.com/inventree/InvenTree/pull/4408
    - Adds "responsible" filter to Build API

v97 -> 2023-02-20 : https://github.com/inventree/InvenTree/pull/4377
    - Adds "external" attribute to StockLocation model

v96 -> 2023-02-16 : https://github.com/inventree/InvenTree/pull/4345
    - Adds stocktake report generation functionality

v95 -> 2023-02-16 : https://github.com/inventree/InvenTree/pull/4346
    - Adds "CompanyAttachment" model (and associated API endpoints)

v94 -> 2023-02-10 : https://github.com/inventree/InvenTree/pull/4327
    - Adds API endpoints for the "Group" auth model

v93 -> 2023-02-03 : https://github.com/inventree/InvenTree/pull/4300
    - Adds extra information to the currency exchange endpoint
    - Adds API endpoint for manually updating exchange rates

v92 -> 2023-02-02 : https://github.com/inventree/InvenTree/pull/4293
    - Adds API endpoint for currency exchange information

v91 -> 2023-01-31 : https://github.com/inventree/InvenTree/pull/4281
    - Improves the API endpoint for creating new Part instances

v90 -> 2023-01-25 : https://github.com/inventree/InvenTree/pull/4186/files
    - Adds a dedicated endpoint to activate a plugin

v89 -> 2023-01-25 : https://github.com/inventree/InvenTree/pull/4214
    - Adds updated field to SupplierPart API
    - Adds API date ordering for supplier part list

v88 -> 2023-01-17: https://github.com/inventree/InvenTree/pull/4225
    - Adds 'priority' field to Build model and api endpoints

v87 -> 2023-01-04 : https://github.com/inventree/InvenTree/pull/4067
    - Add API date filter for stock table on Expiry date

v86 -> 2022-12-22 : https://github.com/inventree/InvenTree/pull/4069
    - Adds API endpoints for part stocktake

v85 -> 2022-12-21 : https://github.com/inventree/InvenTree/pull/3858
    - Add endpoints serving ICS calendars for purchase and sales orders through API

v84 -> 2022-12-21: https://github.com/inventree/InvenTree/pull/4083
    - Add support for listing PO, BO, SO by their reference

v83 -> 2022-11-19 : https://github.com/inventree/InvenTree/pull/3949
    - Add support for structural Stock locations

v82 -> 2022-11-16 : https://github.com/inventree/InvenTree/pull/3931
    - Add support for structural Part categories

v81 -> 2022-11-08 : https://github.com/inventree/InvenTree/pull/3710
    - Adds cached pricing information to Part API
    - Adds cached pricing information to BomItem API
    - Allows Part and BomItem list endpoints to be filtered by 'has_pricing'
    - Remove calculated 'price_string' values from API endpoints
    - Allows PurchaseOrderLineItem API endpoint to be filtered by 'has_pricing'
    - Allows SalesOrderLineItem API endpoint to be filtered by 'has_pricing'
    - Allows SalesOrderLineItem API endpoint to be filtered by 'order_status'
    - Adds more information to SupplierPriceBreak serializer

v80 -> 2022-11-07 : https://github.com/inventree/InvenTree/pull/3906
    - Adds 'barcode_hash' to Part API serializer
    - Adds 'barcode_hash' to StockLocation API serializer
    - Adds 'barcode_hash' to SupplierPart API serializer

v79 -> 2022-11-03 : https://github.com/inventree/InvenTree/pull/3895
    - Add metadata to Company

v78 -> 2022-10-25 : https://github.com/inventree/InvenTree/pull/3854
    - Make PartCategory to be filtered by name and description

v77 -> 2022-10-12 : https://github.com/inventree/InvenTree/pull/3772
    - Adds model permission checks for barcode assignment actions

v76 -> 2022-09-10 : https://github.com/inventree/InvenTree/pull/3640
    - Refactor of barcode data on the API
    - StockItem.uid renamed to StockItem.barcode_hash

v75 -> 2022-09-05 : https://github.com/inventree/InvenTree/pull/3644
    - Adds "pack_size" attribute to SupplierPart API serializer

v74 -> 2022-08-28 : https://github.com/inventree/InvenTree/pull/3615
    - Add confirmation field for completing PurchaseOrder if the order has incomplete lines
    - Add confirmation field for completing SalesOrder if the order has incomplete lines

v73 -> 2022-08-24 : https://github.com/inventree/InvenTree/pull/3605
    - Add 'description' field to PartParameterTemplate model

v72 -> 2022-08-18 : https://github.com/inventree/InvenTree/pull/3567
    - Allow PurchaseOrder to be duplicated via the API

v71 -> 2022-08-18 : https://github.com/inventree/InvenTree/pull/3564
    - Updates to the "part scheduling" API endpoint

v70 -> 2022-08-02 : https://github.com/inventree/InvenTree/pull/3451
    - Adds a 'depth' parameter to the PartCategory list API
    - Adds a 'depth' parameter to the StockLocation list API

v69 -> 2022-08-01 : https://github.com/inventree/InvenTree/pull/3443
    - Updates the PartCategory list API:
        - Improve query efficiency: O(n) becomes O(1)
        - Rename 'parts' field to 'part_count'
    - Updates the StockLocation list API:
        - Improve query efficiency: O(n) becomes O(1)

v68 -> 2022-07-27 : https://github.com/inventree/InvenTree/pull/3417
    - Allows SupplierPart list to be filtered by SKU value
    - Allows SupplierPart list to be filtered by MPN value

v67 -> 2022-07-25 : https://github.com/inventree/InvenTree/pull/3395
    - Adds a 'requirements' endpoint for Part instance
    - Provides information on outstanding order requirements for a given part

v66 -> 2022-07-24 : https://github.com/inventree/InvenTree/pull/3393
    - Part images can now be downloaded from a remote URL via the API
    - Company images can now be downloaded from a remote URL via the API

v65 -> 2022-07-15 : https://github.com/inventree/InvenTree/pull/3335
    - Annotates 'in_stock' quantity to the SupplierPart API

v64 -> 2022-07-08 : https://github.com/inventree/InvenTree/pull/3310
    - Annotate 'on_order' quantity to BOM list API
    - Allow BOM List API endpoint to be filtered by "on_order" parameter

v63 -> 2022-07-06 : https://github.com/inventree/InvenTree/pull/3301
    - Allow BOM List API endpoint to be filtered by "available_stock" parameter

v62 -> 2022-07-05 : https://github.com/inventree/InvenTree/pull/3296
    - Allows search on BOM List API endpoint
    - Allows ordering on BOM List API endpoint

v61 -> 2022-06-12 : https://github.com/inventree/InvenTree/pull/3183
    - Migrate the "Convert Stock Item" form class to use the API
    - There is now an API endpoint for converting a stock item to a valid variant

v60 -> 2022-06-08 : https://github.com/inventree/InvenTree/pull/3148
    - Add availability data fields to the SupplierPart model

v59 -> 2022-06-07 : https://github.com/inventree/InvenTree/pull/3154
    - Adds further improvements to BulkDelete mixin class
    - Fixes multiple bugs in custom OPTIONS metadata implementation
    - Adds 'bulk delete' for Notifications

v58 -> 2022-06-06 : https://github.com/inventree/InvenTree/pull/3146
    - Adds a BulkDelete API mixin class for fast, safe deletion of multiple objects with a single API request

v57 -> 2022-06-05 : https://github.com/inventree/InvenTree/pull/3130
    - Transfer PartCategoryTemplateParameter actions to the API

v56 -> 2022-06-02 : https://github.com/inventree/InvenTree/pull/3123
    - Expose the PartParameterTemplate model to use the API

v55 -> 2022-06-02 : https://github.com/inventree/InvenTree/pull/3120
    - Converts the 'StockItemReturn' functionality to make use of the API

v54 -> 2022-06-02 : https://github.com/inventree/InvenTree/pull/3117
    - Adds 'available_stock' annotation on the SalesOrderLineItem API
    - Adds (well, fixes) 'overdue' annotation on the SalesOrderLineItem API

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
    - API OPTIONS endpoints provide comprehensive field metadata
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
