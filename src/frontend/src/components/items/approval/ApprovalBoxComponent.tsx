import { Trans } from '@lingui/macro';
import { Skeleton, Title } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../../App';
import { ApiPaths, url } from '../../../states/ApiState';
import { ExistingApprovalComponent } from './ExistingApprovalComponent';
import { NewApprovalComponent } from './NewApprovalComponent';

export function ApprovalBoxComponent({ poPK }: { poPK: string }) {
  function fetchData() {
    return api
      .get(
        url(ApiPaths.approval_detail_type, poPK, { type: 'purchase-order' }),
        { params: { user_detail: true } }
      )
      .then((res) => res.data)
      .catch((err) => {
        if (err.response?.status === 404) return [];
        throw err;
      });
  }
  const { isLoading, data, isError, refetch } = useQuery({
    queryKey: [`approval-detail-${poPK}`],
    queryFn: fetchData,
    refetchOnWindowFocus: false
  });
  const ready = !(isLoading || isError);

  return (
    <>
      <Title order={5}>
        <Trans>Approval</Trans>
      </Title>
      {ready ? (
        ready && data.length === 0 ? (
          <NewApprovalComponent poPK={poPK} refetch={refetch} />
        ) : (
          <ExistingApprovalComponent refetch={refetch} data={data} />
        )
      ) : (
        <Skeleton w={'100%'} />
      )}
    </>
  );
}
