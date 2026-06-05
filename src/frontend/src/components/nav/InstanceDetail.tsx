import { Center, Container, Loader } from '@mantine/core';

import type { ModelType } from '@lib/enums/ModelType';
import type { UserRoles } from '@lib/enums/Roles';
import type { UseQueryResult } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { useUserState } from '../../states/UserState';
import ClientError from '../errors/ClientError';
import PermissionDenied from '../errors/PermissionDenied';
import ServerError from '../errors/ServerError';

export default function InstanceDetail({
  query,
  children,
  requiredRole,
  requiredPermission
}: Readonly<{
  query: UseQueryResult;
  children: React.ReactNode;
  requiredRole?: UserRoles;
  requiredPermission?: ModelType;
}>) {
  const user = useUserState();

  const [loaded, setLoaded] = useState<boolean>(false);

  useEffect(() => {
    if (query.isSuccess) {
      setLoaded(true);
    }
  }, [query.isSuccess]);

  if (query.isError) {
    const reason = query.failureReason as any;
    const statusCode = reason?.response?.status ?? reason?.status ?? 0;

    if (statusCode >= 500) {
      return <ServerError status={statusCode} />;
    }

    return <ClientError status={statusCode} />;
  }

  if (requiredRole && !user.hasViewRole(requiredRole)) {
    return <PermissionDenied />;
  }

  if (requiredPermission && !user.hasViewPermission(requiredPermission)) {
    return <PermissionDenied />;
  }

  if (!loaded || !user.isLoggedIn()) {
    // Return a loader for the first page load
    return (
      <Center>
        <Container>
          <Loader />
        </Container>
      </Center>
    );
  }

  return <>{children}</>;
}
