import { Trans } from '@lingui/macro';
import { Code, Title } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';

import { api } from '../../App';
import { PlaceholderPill } from '../../components/items/Placeholder';
import { ApprovalBoxComponent } from '../../components/items/approval/ApprovalBoxComponent';
import { TwoColumnLayout } from '../../components/nav/TwoColumnLayout';
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
    <TwoColumnLayout
      title={<Trans>Purchase Order</Trans>}
      is_placeholder={true}
      sidebar={<ApprovalBoxComponent poPK={poPK} />}
    >
      <Title>
        <Trans>Details for {poPK} here</Trans>
      </Title>
      <PlaceholderPill />
      {!(isLoading || isError) && <Code>{JSON.stringify(data)}</Code>}
    </TwoColumnLayout>
  );
}
