import { t } from '@lingui/macro';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';

export interface ModelInformationInterface {
  url_overview?: string;
  url_detail?: string;
  api_endpoint: ApiEndpoints;
  cui_detail?: string;
  admin_url?: string;
}

// Interface which includes dynamically translated labels
export interface ModelInformationInterfaceWithLabel
  extends ModelInformationInterface {
  label: string;
  label_multiple: string;
}

export type ModelDict = {
  [key in keyof typeof ModelType]: ModelInformationInterface;
};

export const ModelInformationDict: ModelDict = {
  part: {
    url_overview: '/part',
    url_detail: '/part/:pk/',
    cui_detail: '/part/:pk/',
    api_endpoint: ApiEndpoints.part_list,
    admin_url: '/part/part/'
  },
  partparametertemplate: {
    url_overview: '/partparametertemplate',
    url_detail: '/partparametertemplate/:pk/',
    api_endpoint: ApiEndpoints.part_parameter_template_list
  },
  parttesttemplate: {
    url_overview: '/parttesttemplate',
    url_detail: '/parttesttemplate/:pk/',
    api_endpoint: ApiEndpoints.part_test_template_list
  },
  supplierpart: {
    url_overview: '/supplierpart',
    url_detail: '/purchasing/supplier-part/:pk/',
    cui_detail: '/supplier-part/:pk/',
    api_endpoint: ApiEndpoints.supplier_part_list,
    admin_url: '/company/supplierpart/'
  },
  manufacturerpart: {
    url_overview: '/manufacturerpart',
    url_detail: '/purchasing/manufacturer-part/:pk/',
    cui_detail: '/manufacturer-part/:pk/',
    api_endpoint: ApiEndpoints.manufacturer_part_list,
    admin_url: '/company/manufacturerpart/'
  },
  partcategory: {
    url_overview: '/part/category',
    url_detail: '/part/category/:pk/',
    cui_detail: '/part/category/:pk/',
    api_endpoint: ApiEndpoints.category_list,
    admin_url: '/part/partcategory/'
  },
  stockitem: {
    url_overview: '/stock/item',
    url_detail: '/stock/item/:pk/',
    cui_detail: '/stock/item/:pk/',
    api_endpoint: ApiEndpoints.stock_item_list,
    admin_url: '/stock/stockitem/'
  },
  stocklocation: {
    url_overview: '/stock/location',
    url_detail: '/stock/location/:pk/',
    cui_detail: '/stock/location/:pk/',
    api_endpoint: ApiEndpoints.stock_location_list,
    admin_url: '/stock/stocklocation/'
  },
  stocklocationtype: {
    api_endpoint: ApiEndpoints.stock_location_type_list
  },
  stockhistory: {
    api_endpoint: ApiEndpoints.stock_tracking_list
  },
  build: {
    url_overview: '/build',
    url_detail: '/build/:pk/',
    cui_detail: '/build/:pk/',
    api_endpoint: ApiEndpoints.build_order_list,
    admin_url: '/build/build/'
  },
  buildline: {
    url_overview: '/build/line',
    url_detail: '/build/line/:pk/',
    cui_detail: '/build/line/:pk/',
    api_endpoint: ApiEndpoints.build_line_list
  },
  builditem: {
    api_endpoint: ApiEndpoints.build_item_list
  },
  company: {
    url_overview: '/company',
    url_detail: '/company/:pk/',
    cui_detail: '/company/:pk/',
    api_endpoint: ApiEndpoints.company_list,
    admin_url: '/company/company/'
  },
  projectcode: {
    url_overview: '/project-code',
    url_detail: '/project-code/:pk/',
    api_endpoint: ApiEndpoints.project_code_list
  },
  purchaseorder: {
    url_overview: '/purchasing/purchase-order',
    url_detail: '/purchasing/purchase-order/:pk/',
    cui_detail: '/order/purchase-order/:pk/',
    api_endpoint: ApiEndpoints.purchase_order_list,
    admin_url: '/order/purchaseorder/'
  },
  purchaseorderlineitem: {
    api_endpoint: ApiEndpoints.purchase_order_line_list
  },
  salesorder: {
    url_overview: '/sales/sales-order',
    url_detail: '/sales/sales-order/:pk/',
    cui_detail: '/order/sales-order/:pk/',
    api_endpoint: ApiEndpoints.sales_order_list,
    admin_url: '/order/salesorder/'
  },
  salesordershipment: {
    url_overview: '/salesordershipment',
    url_detail: '/salesordershipment/:pk/',
    api_endpoint: ApiEndpoints.sales_order_shipment_list
  },
  returnorder: {
    url_overview: '/sales/return-order',
    url_detail: '/sales/return-order/:pk/',
    cui_detail: '/order/return-order/:pk/',
    api_endpoint: ApiEndpoints.return_order_list,
    admin_url: '/order/returnorder/'
  },
  returnorderlineitem: {
    api_endpoint: ApiEndpoints.return_order_line_list
  },
  address: {
    url_overview: '/address',
    url_detail: '/address/:pk/',
    api_endpoint: ApiEndpoints.address_list
  },
  contact: {
    url_overview: '/contact',
    url_detail: '/contact/:pk/',
    api_endpoint: ApiEndpoints.contact_list
  },
  owner: {
    url_overview: '/owner',
    url_detail: '/owner/:pk/',
    api_endpoint: ApiEndpoints.owner_list
  },
  user: {
    url_overview: '/user',
    url_detail: '/user/:pk/',
    api_endpoint: ApiEndpoints.user_list
  },
  group: {
    url_overview: '/user/group',
    url_detail: '/user/group-:pk',
    api_endpoint: ApiEndpoints.group_list,
    admin_url: '/auth/group/'
  },
  importsession: {
    url_overview: '/import',
    url_detail: '/import/:pk/',
    api_endpoint: ApiEndpoints.import_session_list
  },
  labeltemplate: {
    url_overview: '/labeltemplate',
    url_detail: '/labeltemplate/:pk/',
    api_endpoint: ApiEndpoints.label_list
  },
  reporttemplate: {
    url_overview: '/reporttemplate',
    url_detail: '/reporttemplate/:pk/',
    api_endpoint: ApiEndpoints.report_list
  },
  pluginconfig: {
    url_overview: '/pluginconfig',
    url_detail: '/pluginconfig/:pk/',
    api_endpoint: ApiEndpoints.plugin_list
  },
  contenttype: {
    api_endpoint: ApiEndpoints.content_type_list
  },
  selectionlist: {
    label: t`Selection List`,
    label_multiple: t`Selection Lists`,
    api_endpoint: ApiEndpoints.selectionlist_list
  }
};

/*
 * Return the translated singular label for a particular model type.
 * Note: This *must* be called dynamically, as the translation is not static.
 */
export function getModelLabel(type: ModelType): string {
  switch (type) {
    case ModelType.part:
      return t`Part`;
    case ModelType.partparametertemplate:
      return t`Part Parameter Template`;
    case ModelType.parttesttemplate:
      return t`Part Test Template`;
    case ModelType.supplierpart:
      return t`Supplier Part`;
    case ModelType.manufacturerpart:
      return t`Manufacturer Part`;
    case ModelType.partcategory:
      return t`Part Category`;
    case ModelType.stockitem:
      return t`Stock Item`;
    case ModelType.stocklocation:
      return t`Stock Location`;
    case ModelType.stocklocationtype:
      return t`Stock Location Type`;
    case ModelType.stockhistory:
      return t`Stock History`;
    case ModelType.build:
      return t`Build Order`;
    case ModelType.buildline:
      return t`Build Line`;
    case ModelType.builditem:
      return t`Build Item`;
    case ModelType.company:
      return t`Company`;
    case ModelType.projectcode:
      return t`Project Code`;
    case ModelType.purchaseorder:
      return t`Purchase Order`;
    case ModelType.purchaseorderlineitem:
      return t`Purchase Order Line Item`;
    case ModelType.salesorder:
      return t`Sales Order`;
    case ModelType.salesordershipment:
      return t`Sales Order Shipment`;
    case ModelType.returnorder:
      return t`Return Order`;
    case ModelType.returnorderlineitem:
      return t`Return Order Line Item`;
    case ModelType.address:
      return t`Address`;
    case ModelType.contact:
      return t`Contact`;
    case ModelType.owner:
      return t`Owner`;
    case ModelType.user:
      return t`User`;
    case ModelType.group:
      return t`Group`;
    case ModelType.importsession:
      return t`Import Session`;
    case ModelType.labeltemplate:
      return t`Label Template`;
    case ModelType.reporttemplate:
      return t`Report Template`;
    case ModelType.pluginconfig:
      return t`Plugin Configuration`;
    case ModelType.contenttype:
      return t`Content Type`;
    default:
      return t`Unknown Model`;
  }
}

/*
 * Return the translated plural label for a particular model type.
 * Note: This *must* be called dynamically, as the translation is not static.
 */
export function getModelLabelMultiple(type: ModelType): string {
  switch (type) {
    case ModelType.part:
      return t`Parts`;
    case ModelType.partparametertemplate:
      return t`Part Parameter Templates`;
    case ModelType.parttesttemplate:
      return t`Part Test Templates`;
    case ModelType.supplierpart:
      return t`Supplier Parts`;
    case ModelType.manufacturerpart:
      return t`Manufacturer Parts`;
    case ModelType.partcategory:
      return t`Part Categories`;
    case ModelType.stockitem:
      return t`Stock Items`;
    case ModelType.stocklocation:
      return t`Stock Locations`;
    case ModelType.stocklocationtype:
      return t`Stock Location Types`;
    case ModelType.stockhistory:
      return t`Stock Histories`;
    case ModelType.build:
      return t`Build Orders`;
    case ModelType.buildline:
      return t`Build Lines`;
    case ModelType.builditem:
      return t`Build Items`;
    case ModelType.company:
      return t`Companies`;
    case ModelType.projectcode:
      return t`Project Codes`;
    case ModelType.purchaseorder:
      return t`Purchase Orders`;
    case ModelType.purchaseorderlineitem:
      return t`Purchase Order Line Items`;
    case ModelType.salesorder:
      return t`Sales Orders`;
    case ModelType.salesordershipment:
      return t`Sales Order Shipments`;
    case ModelType.returnorder:
      return t`Return Orders`;
    case ModelType.returnorderlineitem:
      return t`Return Order Line Items`;
    case ModelType.address:
      return t`Addresses`;
    case ModelType.contact:
      return t`Contacts`;
    case ModelType.owner:
      return t`Owners`;
    case ModelType.user:
      return t`Users`;
    case ModelType.group:
      return t`Groups`;
    case ModelType.importsession:
      return t`Import Sessions`;
    case ModelType.labeltemplate:
      return t`Label Templates`;
    case ModelType.reporttemplate:
      return t`Report Templates`;
    case ModelType.pluginconfig:
      return t`Plugin Configurations`;
    case ModelType.contenttype:
      return t`Content Types`;
    default:
      return t`Unknown Models`;
  }
}

/*
 * Extract model definition given the provided type
 * @param type - ModelType to extract information from
 * @returns ModelInformationInterfaceWithLabel
 */
export function getModelInfo(
  type: ModelType
): ModelInformationInterfaceWithLabel {
  return {
    ...ModelInformationDict[type],
    label: getModelLabel(type),
    label_multiple: getModelLabelMultiple(type)
  };
}
