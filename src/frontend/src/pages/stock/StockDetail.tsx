import { t } from '@lingui/macro';
import { Alert, Stack, Text } from '@mantine/core';
import { useParams } from 'react-router-dom';

import { PageDetail } from '../../components/nav/PageDetail';
import { useInstance } from '../../hooks/UseInstance';

export default function StockDetail() {
  const { id } = useParams();

  const {
    instance: stockitem,
    refreshInstance,
    instanceQuery
  } = useInstance('/stock/', id, {
    part_detail: true,
    location_detail: true
  });

  return (
    <Stack>
      <PageDetail
        title={t`Stock Items`}
        subtitle={stockitem.part_detail.full_name}
        detail={
          <Alert color="teal" title="Stock Item">
            <Text>TODO: stock item detail goes here!</Text>
          </Alert>
        }
      />
    </Stack>
  );
}
