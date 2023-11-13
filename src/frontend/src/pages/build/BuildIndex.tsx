import { t } from '@lingui/macro';
import { Button, Stack, Text } from '@mantine/core';
import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageDetail } from '../../components/nav/PageDetail';
import { BuildOrderTable } from '../../components/tables/build/BuildOrderTable';
import { ApiPaths } from '../../enums/ApiEndpoints';
import { buildOrderFields } from '../../forms/BuildForms';
import { openCreateApiForm } from '../../functions/forms';

/**
 * Build Order index page
 */
export default function BuildIndex() {
  const navigate = useNavigate();

  const newBuildOrder = useCallback(() => {
    openCreateApiForm({
      url: ApiPaths.build_order_list,
      title: t`Add Build Order`,
      fields: buildOrderFields(),
      successMessage: t`Build order created`,
      onFormSuccess: (data: any) => {
        if (data.pk) {
          navigate(`/build/${data.pk}`);
        }
      }
    });
  }, []);

  return (
    <>
      <Stack>
        <PageDetail
          title={t`Build Orders`}
          actions={[
            <Button key="new-build" color="green" onClick={newBuildOrder}>
              {t`New Build Order`}
            </Button>
          ]}
        />
        <BuildOrderTable />
      </Stack>
    </>
  );
}
