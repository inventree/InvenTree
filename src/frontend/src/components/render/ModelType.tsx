import { t } from '@lingui/macro';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import type { ModelType } from '../../enums/ModelType';
import type { InvenTreeIconType } from '../../functions/icons';

export interface ModelInformationInterface {
  label: string;
  label_multiple: string;
  url_overview?: string;
  url_detail?: string;
  api_endpoint: ApiEndpoints;
  admin_url?: string;
  icon: InvenTreeIconType;
}

export interface TranslatableModelInformationInterface
  extends Omit<ModelInformationInterface, 'label' | 'label_multiple'> {
  label: () => string;
  label_multiple: () => string;
}

export type ModelDict = {
  [key in keyof typeof ModelType]: TranslatableModelInformationInterface;
};

export const ModelInformationDict: ModelDict = {
  part: {
    label: () => t`Part`,
    label_multiple: () => t`Parts`,
    url_overview: '/part/category/index/parts',
    url_detail: '/part/:pk/',
    api_endpoint: ApiEndpoints.part_list,
    admin_url: '/part/part/',
    icon: 'part'
  },
  partparametertemplate: {
    label: () => t`Part Parameter Template`,
    label_multiple: () => t`Part Parameter Templates`,
    url_overview: '/partparametertemplate',
    url_detail: '/partparametertemplate/:pk/',
    api_endpoint: ApiEndpoints.part_parameter_template_list,
    icon: 'test_templates'
  },
  parttesttemplate: {
    label: () => t`Part Test Template`,
    label_multiple: () => t`Part Test Templates`,
    url_overview: '/parttesttemplate',
    url_detail: '/parttesttemplate/:pk/',
    api_endpoint: ApiEndpoints.part_test_template_list,
    icon: 'test'
  },
  supplierpart: {
    label: () => t`Supplier Part`,
    label_multiple: () => t`Supplier Parts`,
    url_overview: '/supplierpart',
    url_detail: '/purchasing/supplier-part/:pk/',
    api_endpoint: ApiEndpoints.supplier_part_list,
    admin_url: '/company/supplierpart/',
    icon: 'supplier_part'
  },
  manufacturerpart: {
    label: () => t`Manufacturer Part`,
    label_multiple: () => t`Manufacturer Parts`,
    url_overview: '/manufacturerpart',
    url_detail: '/purchasing/manufacturer-part/:pk/',
    api_endpoint: ApiEndpoints.manufacturer_part_list,
    admin_url: '/company/manufacturerpart/',
    icon: 'manufacturers'
  },
  partcategory: {
    label: () => t`Part Category`,
    label_multiple: () => t`Part Categories`,
    url_overview: '/part/category/parts/subcategories',
    url_detail: '/part/category/:pk/',
    api_endpoint: ApiEndpoints.category_list,
    admin_url: '/part/partcategory/',
    icon: 'category'
  },
  stockitem: {
    label: () => t`Stock Item`,
    label_multiple: () => t`Stock Items`,
    url_overview: '/stock/location/index/stock-items',
    url_detail: '/stock/item/:pk/',
    api_endpoint: ApiEndpoints.stock_item_list,
    admin_url: '/stock/stockitem/',
    icon: 'stock'
  },
  stocklocation: {
    label: () => t`Stock Location`,
    label_multiple: () => t`Stock Locations`,
    url_overview: '/stock/location',
    url_detail: '/stock/location/:pk/',
    api_endpoint: ApiEndpoints.stock_location_list,
    admin_url: '/stock/stocklocation/',
    icon: 'location'
  },
  stocklocationtype: {
    label: () => t`Stock Location Type`,
    label_multiple: () => t`Stock Location Types`,
    api_endpoint: ApiEndpoints.stock_location_type_list,
    icon: 'location'
  },
  stockhistory: {
    label: () => t`Stock History`,
    label_multiple: () => t`Stock Histories`,
    api_endpoint: ApiEndpoints.stock_tracking_list,
    icon: 'history'
  },
  build: {
    label: () => t`Build`,
    label_multiple: () => t`Builds`,
    url_overview: '/manufacturing/index/buildorders/',
    url_detail: '/manufacturing/build-order/:pk/',
    api_endpoint: ApiEndpoints.build_order_list,
    admin_url: '/build/build/',
    icon: 'build_order'
  },
  buildline: {
    label: () => t`Build Line`,
    label_multiple: () => t`Build Lines`,
    url_overview: '/build/line',
    url_detail: '/build/line/:pk/',
    api_endpoint: ApiEndpoints.build_line_list,
    icon: 'build_order'
  },
  builditem: {
    label: () => t`Build Item`,
    label_multiple: () => t`Build Items`,
    api_endpoint: ApiEndpoints.build_item_list,
    icon: 'build_order'
  },
  company: {
    label: () => t`Company`,
    label_multiple: () => t`Companies`,
    url_overview: '/company',
    url_detail: '/company/:pk/',
    api_endpoint: ApiEndpoints.company_list,
    admin_url: '/company/company/',
    icon: 'building'
  },
  projectcode: {
    label: () => t`Project Code`,
    label_multiple: () => t`Project Codes`,
    url_overview: '/project-code',
    url_detail: '/project-code/:pk/',
    api_endpoint: ApiEndpoints.project_code_list,
    icon: 'list_details'
  },
  purchaseorder: {
    label: () => t`Purchase Order`,
    label_multiple: () => t`Purchase Orders`,
    url_overview: '/purchasing/index/purchaseorders',
    url_detail: '/purchasing/purchase-order/:pk/',
    api_endpoint: ApiEndpoints.purchase_order_list,
    admin_url: '/order/purchaseorder/',
    icon: 'purchase_orders'
  },
  purchaseorderlineitem: {
    label: () => t`Purchase Order Line`,
    label_multiple: () => t`Purchase Order Lines`,
    api_endpoint: ApiEndpoints.purchase_order_line_list,
    icon: 'purchase_orders'
  },
  salesorder: {
    label: () => t`Sales Order`,
    label_multiple: () => t`Sales Orders`,
    url_overview: '/sales/index/salesorders',
    url_detail: '/sales/sales-order/:pk/',
    api_endpoint: ApiEndpoints.sales_order_list,
    admin_url: '/order/salesorder/',
    icon: 'sales_orders'
  },
  salesordershipment: {
    label: () => t`Sales Order Shipment`,
    label_multiple: () => t`Sales Order Shipments`,
    url_overview: '/sales/shipment/',
    url_detail: '/sales/shipment/:pk/',
    api_endpoint: ApiEndpoints.sales_order_shipment_list,
    icon: 'sales_orders'
  },
  returnorder: {
    label: () => t`Return Order`,
    label_multiple: () => t`Return Orders`,
    url_overview: '/sales/index/returnorders',
    url_detail: '/sales/return-order/:pk/',
    api_endpoint: ApiEndpoints.return_order_list,
    admin_url: '/order/returnorder/',
    icon: 'return_orders'
  },
  returnorderlineitem: {
    label: () => t`Return Order Line Item`,
    label_multiple: () => t`Return Order Line Items`,
    api_endpoint: ApiEndpoints.return_order_line_list,
    icon: 'return_orders'
  },
  address: {
    label: () => t`Address`,
    label_multiple: () => t`Addresses`,
    url_overview: '/address',
    url_detail: '/address/:pk/',
    api_endpoint: ApiEndpoints.address_list,
    icon: 'address'
  },
  contact: {
    label: () => t`Contact`,
    label_multiple: () => t`Contacts`,
    url_overview: '/contact',
    url_detail: '/contact/:pk/',
    api_endpoint: ApiEndpoints.contact_list,
    icon: 'group'
  },
  owner: {
    label: () => t`Owner`,
    label_multiple: () => t`Owners`,
    url_overview: '/owner',
    url_detail: '/owner/:pk/',
    api_endpoint: ApiEndpoints.owner_list,
    icon: 'group'
  },
  user: {
    label: () => t`User`,
    label_multiple: () => t`Users`,
    url_overview: '/user',
    url_detail: '/user/:pk/',
    api_endpoint: ApiEndpoints.user_list,
    icon: 'user'
  },
  group: {
    label: () => t`Group`,
    label_multiple: () => t`Groups`,
    url_overview: '/user/group',
    url_detail: '/user/group-:pk',
    api_endpoint: ApiEndpoints.group_list,
    admin_url: '/auth/group/',
    icon: 'group'
  },
  importsession: {
    label: () => t`Import Session`,
    label_multiple: () => t`Import Sessions`,
    url_overview: '/import',
    url_detail: '/import/:pk/',
    api_endpoint: ApiEndpoints.import_session_list,
    icon: 'import'
  },
  labeltemplate: {
    label: () => t`Label Template`,
    label_multiple: () => t`Label Templates`,
    url_overview: '/labeltemplate',
    url_detail: '/labeltemplate/:pk/',
    api_endpoint: ApiEndpoints.label_list,
    icon: 'labels'
  },
  reporttemplate: {
    label: () => t`Report Template`,
    label_multiple: () => t`Report Templates`,
    url_overview: '/reporttemplate',
    url_detail: '/reporttemplate/:pk/',
    api_endpoint: ApiEndpoints.report_list,
    icon: 'reports'
  },
  pluginconfig: {
    label: () => t`Plugin Configuration`,
    label_multiple: () => t`Plugin Configurations`,
    url_overview: '/pluginconfig',
    url_detail: '/pluginconfig/:pk/',
    api_endpoint: ApiEndpoints.plugin_list,
    icon: 'plugin'
  },
  contenttype: {
    label: () => t`Content Type`,
    label_multiple: () => t`Content Types`,
    api_endpoint: ApiEndpoints.content_type_list,
    icon: 'list_details'
  },
  selectionlist: {
    label: () => t`Selection List`,
    label_multiple: () => t`Selection Lists`,
    api_endpoint: ApiEndpoints.selectionlist_list,
    icon: 'list_details'
  },
  error: {
    label: () => t`Error`,
    label_multiple: () => t`Errors`,
    api_endpoint: ApiEndpoints.error_report_list,
    url_overview: '/settings/admin/errors',
    url_detail: '/settings/admin/errors/:pk/',
    icon: 'exclamation'
  }
};

/*
 * Extract model definition given the provided type - returns translatable strings for labels as string, not functions
 * @param type - ModelType to extract information from
 * @returns ModelInformationInterface
 */
export function getModelInfo(type: ModelType): ModelInformationInterface {
  return {
    ...ModelInformationDict[type],
    label: ModelInformationDict[type].label(),
    label_multiple: ModelInformationDict[type].label_multiple()
  };
}
