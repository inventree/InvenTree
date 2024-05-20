import { style } from '@vanilla-extract/css';

import { vars } from '../../theme';

export const backgroundItem = style({
  maxWidth: '100%',
  padding: '8px',
  boxShadow: vars.shadows.md,
  [vars.lightSelector]: { backgroundColor: vars.colors.white },
  [vars.darkSelector]: { backgroundColor: vars.colors.dark[5] }
});

export const baseItem = style({
  maxWidth: '100%',
  padding: '8px'
});
