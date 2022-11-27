import { ActionIcon } from '@mantine/core';
import { NavLink } from 'react-router-dom';
import InvenTreeIcon from '../../assets/inventree.svg';
import { Trans } from '@lingui/macro'


export function InvenTreeLogo() {
  return (
    <NavLink to={'/'}>
      <ActionIcon size={28}>
        <img src={InvenTreeIcon} alt={<Trans>InvenTree Logo</Trans>} height={28} />
      </ActionIcon>
    </NavLink>
  );
}
