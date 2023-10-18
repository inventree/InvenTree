import { t } from '@lingui/macro';

export enum ModelType {
  part = 'part',
  supplierpart = 'supplierpart',
  manufacturerpart = 'manufacturerpart',
  partcategory = 'partcategory',
  partparametertemplate = 'partparametertemplate',
  stockitem = 'stockitem',
  stocklocation = 'stocklocation',
  build = 'build',
  company = 'company',
  purchaseorder = 'purchaseorder',
  salesorder = 'salesorder',
  salesordershipment = 'salesordershipment',
  returnorder = 'returnorder',
  address = 'address',
  contact = 'contact',
  owner = 'owner',
  user = 'user'
}

interface ModelInformatonInterface {
  label: string;
  label_multiple: string;
  url_overview: string;
  url_detail: string;
}

type ModelDictory = {
  [key in keyof typeof ModelType]: ModelInformatonInterface;
};

export const ModelInformationDict: ModelDictory = {
  part: {
    label: t`Part`,
    label_multiple: t`Parts`,
    url_overview: '/part',
    url_detail: '/part/:pk/'
  },
  partparametertemplate: {
    label: t`Part Parameter Template`,
    label_multiple: t`Part Parameter Templates`,
    url_overview: '/partparametertemplate',
    url_detail: '/partparametertemplate/:pk/'
  },
  supplierpart: {
    label: t`Supplier Part`,
    label_multiple: t`Supplier Parts`,
    url_overview: '/supplierpart',
    url_detail: '/supplierpart/:pk/'
  },
  manufacturerpart: {
    label: t`Manufacturer Part`,
    label_multiple: t`Manufacturer Parts`,
    url_overview: '/manufacturerpart',
    url_detail: '/manufacturerpart/:pk/'
  },
  partcategory: {
    label: t`Part Category`,
    label_multiple: t`Part Categories`,
    url_overview: '/partcategory',
    url_detail: '/partcategory/:pk/'
  },
  stockitem: {
    label: t`Stock Item`,
    label_multiple: t`Stock Items`,
    url_overview: '/stockitem',
    url_detail: '/stockitem/:pk/'
  },
  stocklocation: {
    label: t`Stock Location`,
    label_multiple: t`Stock Locations`,
    url_overview: '/stocklocation',
    url_detail: '/stocklocation/:pk/'
  },
  build: {
    label: t`Build`,
    label_multiple: t`Builds`,
    url_overview: '/build',
    url_detail: '/build/:pk/'
  },
  company: {
    label: t`Company`,
    label_multiple: t`Companies`,
    url_overview: '/company',
    url_detail: '/company/:pk/'
  },
  purchaseorder: {
    label: t`Purchase Order`,
    label_multiple: t`Purchase Orders`,
    url_overview: '/purchaseorder',
    url_detail: '/purchaseorder/:pk/'
  },
  salesorder: {
    label: t`Sales Order`,
    label_multiple: t`Sales Orders`,
    url_overview: '/salesorder',
    url_detail: '/salesorder/:pk/'
  },
  salesordershipment: {
    label: t`Sales Order Shipment`,
    label_multiple: t`Sales Order Shipments`,
    url_overview: '/salesordershipment',
    url_detail: '/salesordershipment/:pk/'
  },
  returnorder: {
    label: t`Return Order`,
    label_multiple: t`Return Orders`,
    url_overview: '/returnorder',
    url_detail: '/returnorder/:pk/'
  },
  address: {
    label: t`Address`,
    label_multiple: t`Addresses`,
    url_overview: '/address',
    url_detail: '/address/:pk/'
  },
  contact: {
    label: t`Contact`,
    label_multiple: t`Contacts`,
    url_overview: '/contact',
    url_detail: '/contact/:pk/'
  },
  owner: {
    label: t`Owner`,
    label_multiple: t`Owners`,
    url_overview: '/owner',
    url_detail: '/owner/:pk/'
  },
  user: {
    label: t`User`,
    label_multiple: t`Users`,
    url_overview: '/user',
    url_detail: '/user/:pk/'
  }
};
