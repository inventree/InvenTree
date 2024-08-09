import { create } from 'zustand';

import { api } from '../App';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from './ApiState';
import { useLocalState } from './LocalState';

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

    const host = useLocalState.getState().host;

    const packs = await api.get(apiUrl(ApiEndpoints.icons));

    await Promise.all(
      packs.data.map(async (pack: any) => {
        const fontName = `inventree-icon-font-${pack.prefix}`;
        const src = Object.entries(pack.fonts as Record<string, string>)
          .map(
            ([format, url]) =>
              `url(${
                url.startsWith('/') ? host + url : url
              }) format("${format}")`
          )
          .join(',\n');
        const font = new FontFace(fontName, src + ';');
        await font.load();
        document.fonts.add(font);

        return font;
      })
    );

    set({
      hasLoaded: true,
      packages: packs.data,
      packagesMap: Object.fromEntries(
        packs.data.map((pack: any) => [pack.prefix, pack])
      )
    });
  }
}));
