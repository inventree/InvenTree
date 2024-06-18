import { formatCurrency } from '../../defaults/formatters';

export function tooltipFormatter(label: any, currency: string) {
  return (
    formatCurrency(label, {
      currency: currency
    })?.toString() ?? ''
  );
}
