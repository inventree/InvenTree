import { t } from '@lingui/core/macro';
import { ActionIcon } from '@mantine/core';
import { type ReactNode, forwardRef } from 'react';
import { NavLink } from 'react-router-dom';

import { useShallow } from 'zustand/react/shallow';
import { useServerApiState } from '../../states/ServerApiState';
import InvenTreeIcon from './inventree.svg';

export const InvenTreeLogoHomeButton = forwardRef<HTMLDivElement>(
  (props, ref) => {
    return (
      <div ref={ref} {...props}>
        <NavLink to={'/'}>
          <ActionIcon size={28} variant='transparent'>
            <InvenTreeLogo />
          </ActionIcon>
        </NavLink>
      </div>
    );
  }
);

/*
 * Render the InvenTree logo
 * - Uses the custom logo if one is defined on the server
 * - Otherwise, uses the default logo
 */
export function InvenTreeLogo(): ReactNode {
  const [server] = useServerApiState(
    useShallow((state) => [state.server, state.fetchServerApiState])
  );

  if (server.server && server.customize?.logo) {
    return (
      <img src={server.customize.logo} alt={t`InvenTree Logo`} height={28} />
    );
  }

  return <img src={InvenTreeIcon} alt={t`InvenTree Logo`} height={28} />;
}
