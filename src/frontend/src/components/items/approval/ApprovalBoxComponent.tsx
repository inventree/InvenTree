import { Trans } from '@lingui/macro';
import { Skeleton, Title } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../../App';
import { ApiPaths, url } from '../../../states/ApiState';
import { ModelType } from '../../render/ModelType';
import { ExistingApprovalComponent } from './ExistingApprovalComponent';
import { NewApprovalComponent } from './NewApprovalComponent';

interface ApprovalBoxInterface {
  model: ModelType;
  pk: string;
}

export function ApprovalBoxComponent({ model, pk }: ApprovalBoxInterface) {
  function fetchData() {
    return api
      .get(url(ApiPaths.approval_detail_type, pk, { type: model }), {
        params: { user_detail: true }
      })
      .then((res) => res.data)
      .catch((err) => {
        if (err.response?.status === 404) return [];
        throw err;
      });
  }
  const { isLoading, data, isError, refetch } = useQuery({
    queryKey: [`approval-detail-${model}-${pk}`],
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
          <NewApprovalComponent poPK={pk} refetch={refetch} />
        ) : (
          <ExistingApprovalComponent refetch={refetch} data={data} />
        )
      ) : (
        <Skeleton w={'100%'} />
      )}
    </>
  );
}
