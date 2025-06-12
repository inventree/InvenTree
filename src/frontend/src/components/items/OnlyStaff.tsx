import { Trans } from '@lingui/react/macro';

import { useShallow } from 'zustand/react/shallow';
import { useUserState } from '../../states/UserState';

export const OnlyStaff = ({ children }: { children: any }) => {
  const [user] = useUserState(useShallow((state) => [state.user]));

  if (user?.is_staff) return children;
  return <Trans>This information is only available for staff users</Trans>;
};
