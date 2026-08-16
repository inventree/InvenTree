import { getStatusCodes } from '../components/render/StatusRenderer';

/**
 * Find the "purchase" cost entry within a StockItem's cost_detail array
 */
export function getPurchaseCost(costDetail?: any[]): any {
  const purchaseKey = getStatusCodes('CostType')?.values?.PURCHASE?.key;
  return costDetail?.find((cost: any) => cost.cost_type === purchaseKey);
}
