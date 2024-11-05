import { t } from '@lingui/macro';
import { Divider, Stack } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { IconReload } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { api } from '../../../../App';
import { ActionButton } from '../../../../components/buttons/ActionButton';
import { FactCollection } from '../../../../components/settings/FactCollection';
import { GlobalSettingList } from '../../../../components/settings/SettingList';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { useTable } from '../../../../hooks/UseTable';
import { apiUrl } from '../../../../states/ApiState';
import { InvenTreeTable } from '../../../../tables/InvenTreeTable';

/*
 * Table for displaying available currencies
 */
export function CurrencyTable({
  setInfo
}: Readonly<{ setInfo: (info: any) => void }>) {
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
        key="refresh"
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
        idAccessor: 'currency',
        tableActions: tableActions,
        dataFormatter: (data: any) => {
          setInfo(data);
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

export default function CurrencyManagmentPanel() {
  const [info, setInfo] = useState<any>({});

  return (
    <Stack gap="xs">
      <FactCollection
        items={[
          { title: t`Last fetched`, value: info?.updated },
          { title: t`Base currency`, value: info?.base_currency }
        ]}
      />
      <Divider />
      <CurrencyTable setInfo={setInfo} />
      <Divider />
      <GlobalSettingList
        keys={['CURRENCY_UPDATE_PLUGIN', 'CURRENCY_UPDATE_INTERVAL']}
      />
    </Stack>
  );
}
