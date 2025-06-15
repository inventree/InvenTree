import { style } from '@vanilla-extract/css';
import { vars } from '../../theme';

export const selectedPanelTab = style({
  selectors: {
    '&[data-active]': {
      background: vars.colors.primaryColors.light
    }
  }
});

export const selectedPanelTabLabel = style({
  textAlign: 'left'
});
