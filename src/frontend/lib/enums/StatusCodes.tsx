import { ModelType } from './ModelType';

/**
 * List of status codes which are used in the backend
 * and the model type they are associated with
 */
export const statusCodeList: Record<string, ModelType> = {
  BuildStatus: ModelType.build,
  PurchaseOrderStatus: ModelType.purchaseorder,
  ReturnOrderStatus: ModelType.returnorder,
  ReturnOrderLineStatus: ModelType.returnorderlineitem,
  SalesOrderStatus: ModelType.salesorder,
  StockHistoryCode: ModelType.stockhistory,
  StockStatus: ModelType.stockitem,
  DataImportStatusCode: ModelType.importsession
};

/*
 * Map the colors used in the backend to the colors used in the frontend
 */
export const statusColorMap: { [key: string]: string } = {
  dark: 'dark',
  warning: 'yellow',
  success: 'green',
  info: 'cyan',
  danger: 'red',
  primary: 'blue',
  secondary: 'gray',
  default: 'gray'
};

export interface StatusCodeInterface {
  key: number;
  label: string;
  name: string;
  color: string;
}

export interface StatusCodeListInterface {
  status_class: string;
  values: {
    [key: string]: StatusCodeInterface;
  };
}

export type StatusLookup = Record<ModelType | string, StatusCodeListInterface>;
