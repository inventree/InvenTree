import { LoadingOverlay } from '@mantine/core';

import type { ModelType } from '../../enums/ModelType';
import type { UserRoles } from '../../enums/Roles';
import { useUserState } from '../../states/UserState';
import ClientError from '../errors/ClientError';
import PermissionDenied from '../errors/PermissionDenied';
import ServerError from '../errors/ServerError';

export default function InstanceDetail({
  status,
  loading,
  children,
  requiredRole,
  requiredPermission
}: Readonly<{
  status: number;
  loading: boolean;
  children: React.ReactNode;
  requiredRole?: UserRoles;
  requiredPermission?: ModelType;
}>) {
  const user = useUserState();

  if (loading || !user.isLoggedIn()) {
    return <LoadingOverlay />;
  }

  if (status >= 500) {
    return <ServerError status={status} />;
  }

  if (status >= 400) {
    return <ClientError status={status} />;
  }

  if (requiredRole && !user.hasViewRole(requiredRole)) {
    return <PermissionDenied />;
  }

  if (requiredPermission && !user.hasViewPermission(requiredPermission)) {
    return <PermissionDenied />;
  }

  return <>{children}</>;
}
