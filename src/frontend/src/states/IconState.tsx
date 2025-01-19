import { create } from 'zustand';

import { t } from '@lingui/macro';
import { showNotification } from '@mantine/notifications';
import { api } from '../App';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { generateUrl } from '../functions/urls';
import { apiUrl } from './ApiState';

type IconPackage = {
  name: string;
  prefix: string;
  fonts: Record<string, string>;
  icons: Record<
    string,
    {
      name: string;
      category: string;
      tags: string[];
      variants: Record<string, string>;
    }
  >;
};

type IconState = {
  hasLoaded: boolean;
  packages: IconPackage[];
  packagesMap: Record<string, IconPackage>;
  fetchIcons: () => Promise<void>;
};

export const useIconState = create<IconState>()((set, get) => ({
  hasLoaded: false,
  packages: [],
  packagesMap: {},
  fetchIcons: async () => {
    if (get().hasLoaded) return;

    const packs = await api.get(apiUrl(ApiEndpoints.icons)).catch((_error) => {
      console.error('ERR: Could not fetch icon packages');
      showNotification({
        title: t`Error`,
        message: t`Error loading icon package from server`,
        color: 'red'
      });
    });

    if (!packs) {
      return;
    }

    await Promise.all(
      packs.data.map(async (pack: any) => {
        if (pack.prefix && pack.fonts) {
          const fontName = `inventree-icon-font-${pack.prefix}`;
          const src = Object.entries(pack.fonts as Record<string, string>)
            .map(
              ([format, url]) => `url(${generateUrl(url)}) format("${format}")`
            )
            .join(',\n');
          const font = new FontFace(fontName, `${src};`);
          await font.load();
          document.fonts.add(font);
          return font;
        } else {
          console.error(
            "ERR: Icon package is missing 'prefix' or 'fonts' field"
          );
          showNotification({
            title: t`Error`,
            message: t`Error loading icon package from server`,
            color: 'red'
          });

          return null;
        }
      })
    );

    set({
      hasLoaded: true,
      packages: packs.data,
      packagesMap: Object.fromEntries(
        packs.data?.map((pack: any) => [pack.prefix, pack])
      )
    });
  }
}));
