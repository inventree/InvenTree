import { t } from '@lingui/macro';

import { ApiPaths } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';

interface ModelInformationInterface {
  label: string;
  label_multiple: string;
  url_overview?: string;
  url_detail?: string;
  api_endpoint?: ApiPaths;
  cui_detail?: string;
}

type ModelDictory = {
  [key in keyof typeof ModelType]: ModelInformationInterface;
};

export const ModelInformationDict: ModelDictory = {
  part: {
    label: t`Part`,
    label_multiple: t`Parts`,
    url_overview: '/part',
    url_detail: '/part/:pk/',
    cui_detail: '/part/:pk/',
    api_endpoint: ApiPaths.part_list
  },
  partparametertemplate: {
    label: t`Part Parameter Template`,
    label_multiple: t`Part Parameter Templates`,
    url_overview: '/partparametertemplate',
    url_detail: '/partparametertemplate/:pk/',
    api_endpoint: ApiPaths.part_parameter_template_list
  },
  supplierpart: {
    label: t`Supplier Part`,
    label_multiple: t`Supplier Parts`,
    url_overview: '/supplierpart',
    url_detail: '/purchasing/supplier-part/:pk/',
    cui_detail: '/supplier-part/:pk/',
    api_endpoint: ApiPaths.supplier_part_list
  },
  manufacturerpart: {
    label: t`Manufacturer Part`,
    label_multiple: t`Manufacturer Parts`,
    url_overview: '/manufacturerpart',
    url_detail: '/purchasing/manufacturer-part/:pk/',
    cui_detail: '/manufacturer-part/:pk/',
    api_endpoint: ApiPaths.manufacturer_part_list
  },
  partcategory: {
    label: t`Part Category`,
    label_multiple: t`Part Categories`,
    url_overview: '/partcategory',
    url_detail: '/partcategory/:pk/',
    cui_detail: '/part/category/:pk/',
    api_endpoint: ApiPaths.category_list
  },
  stockitem: {
    label: t`Stock Item`,
    label_multiple: t`Stock Items`,
    url_overview: '/stock/item',
    url_detail: '/stock/item/:pk/',
    cui_detail: '/stock/item/:pk/',
    api_endpoint: ApiPaths.stock_item_list
  },
  stocklocation: {
    label: t`Stock Location`,
    label_multiple: t`Stock Locations`,
    url_overview: '/stock/location',
    url_detail: '/stock/location/:pk/',
    cui_detail: '/stock/location/:pk/',
    api_endpoint: ApiPaths.stock_location_list
  },
  stockhistory: {
    label: t`Stock History`,
    label_multiple: t`Stock Histories`,
    api_endpoint: ApiPaths.stock_tracking_list
  },
  build: {
    label: t`Build`,
    label_multiple: t`Builds`,
    url_overview: '/build',
    url_detail: '/build/:pk/',
    cui_detail: '/build/:pk/',
    api_endpoint: ApiPaths.build_order_list
  },
  company: {
    label: t`Company`,
    label_multiple: t`Companies`,
    url_overview: '/company',
    url_detail: '/company/:pk/',
    cui_detail: '/company/:pk/',
    api_endpoint: ApiPaths.company_list
  },
  projectcode: {
    label: t`Project Code`,
    label_multiple: t`Project Codes`,
    url_overview: '/project-code',
    url_detail: '/project-code/:pk/',
    api_endpoint: ApiPaths.project_code_list
  },
  purchaseorder: {
    label: t`Purchase Order`,
    label_multiple: t`Purchase Orders`,
    url_overview: '/purchasing/purchase-order',
    url_detail: '/purchasing/purchase-order/:pk/',
    cui_detail: '/order/purchase-order/:pk/',
    api_endpoint: ApiPaths.purchase_order_list
  },
  purchaseorderline: {
    label: t`Purchase Order Line`,
    label_multiple: t`Purchase Order Lines`,
    api_endpoint: ApiPaths.purchase_order_line_list
  },
  salesorder: {
    label: t`Sales Order`,
    label_multiple: t`Sales Orders`,
    url_overview: '/sales/sales-order',
    url_detail: '/sales/sales-order/:pk/',
    cui_detail: '/order/sales-order/:pk/',
    api_endpoint: ApiPaths.sales_order_list
  },
  salesordershipment: {
    label: t`Sales Order Shipment`,
    label_multiple: t`Sales Order Shipments`,
    url_overview: '/salesordershipment',
    url_detail: '/salesordershipment/:pk/',
    api_endpoint: ApiPaths.sales_order_shipment_list
  },
  returnorder: {
    label: t`Return Order`,
    label_multiple: t`Return Orders`,
    url_overview: '/sales/return-order',
    url_detail: '/sales/return-order/:pk/',
    cui_detail: '/order/return-order/:pk/',
    api_endpoint: ApiPaths.return_order_list
  },
  address: {
    label: t`Address`,
    label_multiple: t`Addresses`,
    url_overview: '/address',
    url_detail: '/address/:pk/',
    api_endpoint: ApiPaths.address_list
  },
  contact: {
    label: t`Contact`,
    label_multiple: t`Contacts`,
    url_overview: '/contact',
    url_detail: '/contact/:pk/',
    api_endpoint: ApiPaths.contact_list
  },
  owner: {
    label: t`Owner`,
    label_multiple: t`Owners`,
    url_overview: '/owner',
    url_detail: '/owner/:pk/',
    api_endpoint: ApiPaths.owner_list
  },
  user: {
    label: t`User`,
    label_multiple: t`Users`,
    url_overview: '/user',
    url_detail: '/user/:pk/',
    api_endpoint: ApiPaths.user_list
  }
};
