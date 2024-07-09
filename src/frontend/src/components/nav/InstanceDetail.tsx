import { LoadingOverlay } from '@mantine/core';

import ClientError from '../errors/ClientError';
import ServerError from '../errors/ServerError';

export default function InstanceDetail({
  status,
  loading,
  children
}: {
  status: number;
  loading: boolean;
  children: React.ReactNode;
}) {
  if (loading) {
    return <LoadingOverlay />;
  }

  if (status >= 500) {
    return <ServerError status={status} />;
  }

  if (status >= 400) {
    return <ClientError status={status} />;
  }

  return <>{children}</>;
}
