import { create } from 'zustand';

import { ApiEndpoints } from '@lib/core';
import { apiUrl, generateUrl } from '@lib/functions';
import { getApi } from '@lib/functions/api';
import { t } from '@lingui/macro';
import { hideNotification, showNotification } from '@mantine/notifications';

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

    const api = getApi();

    const packs = await api.get(apiUrl(ApiEndpoints.icons)).catch((_error) => {
      console.error('ERR: Could not fetch icon packages');

      hideNotification('icon-fetch-error');

      showNotification({
        id: 'icon-fetch-error',
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
          hideNotification('icon-fetch-error');
          showNotification({
            id: 'icon-fetch-error',
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
