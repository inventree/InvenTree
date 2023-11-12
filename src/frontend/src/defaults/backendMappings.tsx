import { ModelType } from '../enums/ModelType';

/* Lookup tables for mapping backend responses to internal types */

/**
 * List of status codes which are used in the backend
 * and the model type they are associated with
 */
export const statusCodeList: Record<string, ModelType> = {
  BuildStatus: ModelType.build,
  PurchaseOrderStatus: ModelType.purchaseorder,
  ReturnOrderLineStatus: ModelType.purchaseorderline,
  ReturnOrderStatus: ModelType.returnorder,
  SalesOrderStatus: ModelType.salesorder,
  StockHistoryCode: ModelType.stockhistory,
  StockStatus: ModelType.stockitem
};

/*
 * Map the colors used in the backend to the colors used in the frontend
 */
export const colorMap: { [key: string]: string } = {
  dark: 'dark',
  warning: 'yellow',
  success: 'green',
  info: 'cyan',
  danger: 'red',
  default: 'gray'
};
