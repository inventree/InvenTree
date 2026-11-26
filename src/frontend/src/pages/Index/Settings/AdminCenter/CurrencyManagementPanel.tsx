import { t } from '@lingui/core/macro';
import { ActionIcon, Divider, Menu, Stack, Tooltip } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { IconDotsVertical, IconEdit, IconRefresh } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import { api } from '../../../../App';
import { FactCollection } from '../../../../components/settings/FactCollection';
import { GlobalSettingList } from '../../../../components/settings/SettingList';
import { InvenTreeTable } from '../../../../components/tables/InvenTreeTable';
import { showApiErrorMessage } from '../../../../functions/notifications';
import { useEditApiFormModal } from '../../../../hooks/UseForm';
import { useGlobalSettingsState } from '../../../../states/SettingsStates';

/*
 * Table for displaying available currencies
 */
export function CurrencyTable({
  setInfo
}: Readonly<{ setInfo: (info: any) => void }>) {
  const table = useTable('currency', { idAccessor: 'currency' });
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
          title: t`Success`,
          message: t`Exchange rates updated`,
          color: 'green'
        });
      })
      .catch((error) => {
        showApiErrorMessage({
          error: error,
          title: t`Exchange rate update error`
        });
      });
  }, []);

  const globalSettings = useGlobalSettingsState();
  const currenciesSettings = globalSettings.settings.find(
    (setting) => setting.key === 'CURRENCY_CODES'
  );

  const editCurrenciesModal = useEditApiFormModal({
    url: globalSettings.endpoint,
    pk: 'CURRENCY_CODES',
    title: t`Edit currencies`,
    fields: {
      value: {
        field_type: 'string',
        required: true,
        label: currenciesSettings?.name,
        description: currenciesSettings?.description,
        api_url: currenciesSettings?.api_url ?? ''
      }
    },
    successMessage: t`Base currency updated`,
    onFormSuccess: () => globalSettings.fetchSettings()
  });

  const tableActions = useMemo(() => {
    return [
      <Menu position='bottom-end'>
        <Menu.Target>
          <ActionIcon variant='subtle' aria-label={t`Currency actions`}>
            <IconDotsVertical />
          </ActionIcon>
        </Menu.Target>
        <Menu.Dropdown>
          <Menu.Item
            leftSection={<IconRefresh size={16} />}
            onClick={refreshCurrencies}
          >{t`Refresh currency exchange rates`}</Menu.Item>
          <Menu.Item
            leftSection={<IconEdit size={16} />}
            onClick={() => editCurrenciesModal.open()}
          >{t`Edit supported currencies`}</Menu.Item>
        </Menu.Dropdown>
      </Menu>
    ];
  }, []);

  return (
    <>
      {editCurrenciesModal.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.currency_list)}
        tableState={table}
        columns={columns}
        props={{
          tableActions: tableActions,
          dataFormatter: (data: any) => {
            setInfo(data);
            const rates = data.exchange_rates ?? {};

            return Object.entries(rates).map(([currency, rate]) => {
              return {
                currency: currency,
                rate: rate
              };
            });
          }
        }}
      />
    </>
  );
}

export default function CurrencyManagementPanel() {
  const [info, setInfo] = useState<any>({});
  const globalSettings = useGlobalSettingsState();
  const baseCurrencySetting = globalSettings.settings.find(
    (setting) => setting.key === 'INVENTREE_DEFAULT_CURRENCY'
  );
  const editBaseCurrencyModal = useEditApiFormModal({
    url: globalSettings.endpoint,
    pk: 'INVENTREE_DEFAULT_CURRENCY',
    title: t`Edit base currency`,
    fields: {
      value: {
        field_type: 'choice',
        required: true,
        label: baseCurrencySetting?.name,
        description: baseCurrencySetting?.description,
        api_url: baseCurrencySetting?.api_url ?? '',
        choices: baseCurrencySetting?.choices ?? undefined
      }
    },
    successMessage: t`Base currency updated`,
    onFormSuccess: () => globalSettings.fetchSettings()
  });

  return (
    <Stack gap='xs'>
      {editBaseCurrencyModal.modal}
      <FactCollection
        items={[
          { title: t`Last fetched`, value: info?.updated },
          {
            title: t`Base currency`,
            value: info?.base_currency,
            action: (
              <Tooltip label={t`Edit base currency`}>
                <ActionIcon
                  variant='subtle'
                  aria-label={t`Edit base currency`}
                  onClick={() => editBaseCurrencyModal.open()}
                >
                  <IconEdit size={16} />
                </ActionIcon>
              </Tooltip>
            )
          }
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
