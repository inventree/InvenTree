import { style } from '@vanilla-extract/css';

export const icon = style({
  fontStyle: 'normal',
  fontWeight: 'normal',
  fontVariant: 'normal',
  textTransform: 'none',
  lineHeight: 1,
  width: 'fit-content',
  // Better font rendering
  WebkitFontSmoothing: 'antialiased',
  MozOsxFontSmoothing: 'grayscale'
});
