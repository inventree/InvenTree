import { Trans } from '@lingui/macro';
import { Code, Container, Grid, Group, Title } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';

import { api } from '../../App';
import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import { ApprovalBoxComponent } from '../../components/items/approval/ApprovalBoxComponent';
import { ApiPaths, url } from '../../states/ApiState';
import ErrorPage from '../ErrorPage';

export default function PurchaseOrderDetail() {
  const { pk: poPK } = useParams();
  function fetchData() {
    return api.get(url(ApiPaths.po_detail, poPK)).then((res) => res.data);
  }
  const { isLoading, data, isError } = useQuery({
    queryKey: [`part-detail-${poPK}`],
    queryFn: fetchData,
    refetchOnWindowFocus: false
  });

  if (poPK === undefined) {
    return <ErrorPage />;
  }

  return (
    <>
      <Group>
        <StylishText>
          <Trans>Purchase Order</Trans>
        </StylishText>
        <PlaceholderPill />
      </Group>
      <Grid grow>
        <Grid.Col span={8} sx={{ overflow: 'auto' }}>
          <Title>
            <Trans>Details for {poPK} here</Trans>
          </Title>
          <PlaceholderPill />
          {!(isLoading || isError) && <Code>{JSON.stringify(data)}</Code>}
        </Grid.Col>
        <Grid.Col span={2} sx={{ overflow: 'auto' }}>
          <ApprovalBoxComponent poPK={poPK} />
        </Grid.Col>
      </Grid>
    </>
  );
}
