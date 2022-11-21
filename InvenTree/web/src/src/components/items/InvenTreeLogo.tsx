import { ActionIcon } from '@mantine/core';
import { NavLink } from 'react-router-dom';
import InvenTreeIcon from '../../assets/inventree.svg';


export function InvenTreeLogo() {
  return <NavLink to={'/'}><ActionIcon size={28}><img src={InvenTreeIcon} alt="InvenTree Logo" height={28} /></ActionIcon></NavLink>;
}
