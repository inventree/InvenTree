import { rem } from '@mantine/core';
import { style } from '@vanilla-extract/css';

import { vars } from '../../theme';

export const backgroundItem = style({
  backgroundColor:
    //theme.colorScheme === 'dark' ? vars.colors.dark[5] : vars.white,
    vars.colors.white,
  maxWidth: '100%',
  padding: '8px',
  boxShadow: vars.shadows.md
});

export const baseItem = style({
  maxWidth: '100%',
  padding: '8px'
});
