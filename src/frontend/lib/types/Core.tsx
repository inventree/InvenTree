import type { MantineRadius, MantineSize } from '@mantine/core';

export type UiSizeType = MantineSize | string | number;

export interface UserTheme {
  primaryColor: string;
  whiteColor: string;
  blackColor: string;
  radius: MantineRadius;
  loader: string;
}

export type PathParams = Record<string, string | number>;

export type TippData = {
  title: string;
  color: string;
  text: string;
};
