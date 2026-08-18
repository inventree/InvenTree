import { ModelType } from '@lib/enums/ModelType';

/* Lookup tables for mapping backend responses to internal types */

/**
 * List of status codes which are used in the backend
 * and the model type they are associated with
 */
export const statusCodeList: Record<string, ModelType> = {
  BuildStatus: ModelType.build,
  NonConformanceStatus: ModelType.nonconformance,
  PurchaseOrderStatus: ModelType.purchaseorder,
  ReturnOrderStatus: ModelType.returnorder,
  ReturnOrderLineStatus: ModelType.returnorderlineitem,
  TransferOrderStatus: ModelType.transferorder,
  TransferOrderLineStatus: ModelType.transferorderlineitem,
  SalesOrderStatus: ModelType.salesorder,
  StockHistoryCode: ModelType.stockhistory,
  StockStatus: ModelType.stockitem,
  DataImportStatusCode: ModelType.importsession
};

/**
 * NonConformance has a second, independent status-code field ('disposition') on the
 * same model. There is no separate ModelType for it (it isn't a navigable entity of its
 * own), so it is deliberately left out of statusCodeList above - callers reference the
 * raw backend status-class name directly instead of a ModelType.
 */
export const ncrDispositionStatusType = 'NonConformanceDisposition';

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
