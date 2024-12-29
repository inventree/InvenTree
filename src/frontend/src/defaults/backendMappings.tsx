import { ModelType } from '../enums/ModelType';

/* Lookup tables for mapping backend responses to internal types */

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
