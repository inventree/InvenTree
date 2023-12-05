import { t } from '@lingui/macro';
import { ActionIcon } from '@mantine/core';
import { forwardRef } from 'react';
import { NavLink } from 'react-router-dom';

import InvenTreeIcon from './inventree.svg';

export const InvenTreeLogoHomeButton = forwardRef<HTMLDivElement>(
  (props, ref) => {
    return (
      <div ref={ref} {...props}>
        <NavLink to={'/'}>
          <ActionIcon size={28}>
            <InvenTreeLogo />
          </ActionIcon>
        </NavLink>
      </div>
    );
  }
);

export const InvenTreeLogo = () => {
  return <img src={InvenTreeIcon} alt={t`InvenTree Logo`} height={28} />;
};
