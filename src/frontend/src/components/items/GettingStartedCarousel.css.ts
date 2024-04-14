import { rem } from '@mantine/core';
import { style } from '@vanilla-extract/css';

import { vars } from '../../theme';

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
  color:
    //vars.colorScheme === 'dark' ? vars.colors.white[0] : vars.colors.dark[0],
    vars.colors.dark[0],
  lineHeight: 1.2,
  fontSize: rem(32),
  marginTop: 0
});

export const category = style({
  color:
    //vars.colorScheme === 'dark' ? vars.colors.white : vars.colors.dark,
    vars.colors.dark[0],
  opacity: 0.7,
  fontWeight: 700
});
