import { style } from '@vanilla-extract/css';

import { themeVars } from '@lib/index';

export const button = style({
  borderTopRightRadius: 0,
  borderBottomRightRadius: 0,

  ':before': {
    borderRadius: '0 !important'
  }
});

export const icon = style({
  borderTopLeftRadius: 0,
  borderBottomLeftRadius: 0,
  border: 0,
  borderLeft: `1px solid ${themeVars.colors.primaryShade}`
});
