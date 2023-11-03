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
          <InvenTreeLogo />
        </NavLink>
      </div>
    );
  }
);

export const InvenTreeLogo = () => {
  return (
    <ActionIcon size={28}>
      <img src={InvenTreeIcon} alt={t`InvenTree Logo`} height={28} />
    </ActionIcon>
  );
};
