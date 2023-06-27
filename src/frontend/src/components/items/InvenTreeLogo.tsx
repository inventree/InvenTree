import { ActionIcon } from '@mantine/core';
import { NavLink } from 'react-router-dom';
import InvenTreeIcon from './inventree.svg';
import { t } from '@lingui/macro';

export function InvenTreeLogo() {
  return (
    <NavLink to={'/'}>
      <ActionIcon size={28}>
        <img src={InvenTreeIcon} alt={t`InvenTree Logo`} height={28} />
      </ActionIcon>
    </NavLink>
  );
}
