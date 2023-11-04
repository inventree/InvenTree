import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { InvenTreeTable } from '../InvenTreeTable';

/*
 * Table for displaying available currencies
 */
export function CurrencyTable() {
  const { tableKey, refreshTable } = useTableRefresh('currency');

  const columns = useMemo(() => {
    return [
      {
        accessor: 'currency',
        title: t`Currency`,
        switchable: false
      },
      {
        accessor: 'rate',
        title: t`Rate`,
        switchable: false
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.currency_list)}
      tableKey={tableKey}
      columns={columns}
      props={{
        dataFormatter: (data) => {
          let rates = data?.exchange_rates ?? {};

          return Object.entries(rates).map(([currency, rate]) => {
            return {
              currency: currency,
              rate: rate
            };
          });
        }
      }}
    />
  );
}
