import { formatCurrency } from '../../defaults/formatters';

/*
 * Render a chart label for a currency graph
 */
export function tooltipFormatter(value: any, currency?: string) {
  return (
    formatCurrency(value, {
      currency: currency
    })?.toString() ?? value.toString()
  );
}
