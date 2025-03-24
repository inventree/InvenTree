import { rem } from '@mantine/core';
import { style } from '@vanilla-extract/css';

import { themeVars } from '@lib/core';

export const card = style({
  height: rem(170),
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between',
  alignItems: 'flex-start',
  backgroundSize: 'cover',
  backgroundPosition: 'center'
});

export const title = style({
  fontWeight: 900,
  lineHeight: 1.2,
  fontSize: rem(32),
  marginTop: 0,
  [themeVars.lightSelector]: { color: themeVars.colors.dark[5] },
  [themeVars.darkSelector]: { color: themeVars.colors.white[0] }
});

export const category = style({
  opacity: 0.7,
  fontWeight: 700,
  [themeVars.lightSelector]: { color: themeVars.colors.dark[5] },
  [themeVars.darkSelector]: { color: themeVars.colors.white[0] }
});
