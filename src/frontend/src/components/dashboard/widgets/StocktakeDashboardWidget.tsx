import { ApiEndpoints, UserRoles, apiUrl } from '@lib/index';
import { t } from '@lingui/core/macro';
import { Button, Stack } from '@mantine/core';
import { IconClipboardList } from '@tabler/icons-react';
import { useState } from 'react';
import useDataOutput from '../../../hooks/UseDataOutput';
import { useCreateApiFormModal } from '../../../hooks/UseForm';
import { useUserState } from '../../../states/UserState';
import type { DashboardWidgetProps } from '../DashboardWidget';

function StocktakeWidget() {
  const [outputId, setOutputId] = useState<number | undefined>(undefined);

  useDataOutput({
    title: t`Generating Stocktake Report`,
    id: outputId
  });

  const stocktakeForm = useCreateApiFormModal({
    title: t`Generate Stocktake Report`,
    url: apiUrl(ApiEndpoints.part_stocktake_generate),
    fields: {
      part: {
        filters: {
          active: true
        }
      },
      category: {},
      location: {},
      generate_entry: {
        value: false
      },
      generate_report: {
        value: true
      }
    },
    submitText: t`Generate`,
    successMessage: null,
    onFormSuccess: (response) => {
      if (response.output?.pk) {
        setOutputId(response.output.pk);
      }
    }
  });

  return (
    <>
      {stocktakeForm.modal}
      <Stack gap='xs'>
        <Button
          leftSection={<IconClipboardList />}
          onClick={() => stocktakeForm.open()}
        >{t`Generate Stocktake Report`}</Button>
      </Stack>
    </>
  );
}

export default function StocktakeDashboardWidget(): DashboardWidgetProps {
  const user = useUserState();

  return {
    label: 'stk',
    title: t`Stocktake`,
    description: t`Generate a new stocktake report`,
    minHeight: 1,
    minWidth: 2,
    render: () => <StocktakeWidget />,
    enabled: user.hasAddRole(UserRoles.part)
  };
}
