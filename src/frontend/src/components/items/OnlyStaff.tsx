import { Trans } from '@lingui/macro';

import { useUserState } from '../../states/UserState';

export const OnlyStaff = ({ children }: { children: any }) => {
  const [user] = useUserState((state) => [state.user]);

  if (user?.is_staff) return children;
  return <Trans>This information is only available for staff users</Trans>;
};
