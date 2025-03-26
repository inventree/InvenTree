import { themeVars } from '@lib/index';
import { style } from '@vanilla-extract/css';

export const selectedPanelTab = style({
  selectors: {
    '&[data-active]': {
      background: themeVars.colors.primaryColors.light
    }
  }
});
