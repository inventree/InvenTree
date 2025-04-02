import type { MantineSize } from '@mantine/core';

export type UiSizeType = MantineSize | string | number;

export interface UserTheme {
  primaryColor: string;
  whiteColor: string;
  blackColor: string;
  radius: UiSizeType;
  loader: string;
}

export type PathParams = Record<string, string | number>;
