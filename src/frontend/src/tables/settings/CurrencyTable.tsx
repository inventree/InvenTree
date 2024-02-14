import { t } from '@lingui/macro';
import { showNotification } from '@mantine/notifications';
import { IconReload } from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';

import { api } from '../../App';
import { ActionButton } from '../../components/buttons/ActionButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { InvenTreeTable } from '../InvenTreeTable';

/*
 * Table for displaying available currencies
 */
export function CurrencyTable() {
  const table = useTable('currency');

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

  const refreshCurrencies = useCallback(() => {
    api
      .post(apiUrl(ApiEndpoints.currency_refresh), {})
      .then(() => {
        table.refreshTable();
        showNotification({
          message: t`Exchange rates updated`,
          color: 'green'
        });
      })
      .catch((error) => {
        showNotification({
          title: t`Exchange rate update error`,
          message: error,
          color: 'red'
        });
      });
  }, []);

  const tableActions = useMemo(() => {
    return [
      <ActionButton
        onClick={refreshCurrencies}
        tooltip={t`Refresh currency exchange rates`}
        icon={<IconReload />}
      />
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.currency_list)}
      tableState={table}
      columns={columns}
      props={{
        tableActions: tableActions,
        dataFormatter: (data: any) => {
          let rates = data.exchange_rates ?? {};

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
