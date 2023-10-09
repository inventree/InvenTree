import { createContext, useMemo } from 'react';

import { useInstance } from '../hooks/UseInstance';
import { ApiPaths, url } from '../states/ApiState';
import { UserProps } from '../states/states';

/**
 * Custom context provider,
 * which allows any component to access user information
 */

export const UserContext = createContext<UserProps | null>(null);

export function InvenTreeUserContext({ children }: { children: JSX.Element }) {
  // Base query manager for user information
  const { instance: userInstance } = useInstance({
    url: url(ApiPaths.user_me),
    hasPrimaryKey: false,
    defaultValue: {},
    fetchOnMount: true
  });

  // Transform returned user data into a UserProps object
  const user: UserProps | null = useMemo(() => {
    if (!userInstance) {
      return null;
    } else {
      return {
        name: `${userInstance.first_name} ${userInstance.last_name}`,
        email: userInstance.email,
        username: userInstance.username,
        is_staff: userInstance.is_staff ?? false,
        is_superuser: userInstance.is_superuser ?? false
      };
    }
  }, [userInstance]);

  return <UserContext.Provider value={user}>{children}</UserContext.Provider>;
}
