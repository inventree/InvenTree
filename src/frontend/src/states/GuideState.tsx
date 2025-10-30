import { create } from 'zustand';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { TippData } from '@lib/types/Core';
import { api } from '../App';

type GuideState = {
  hasLoaded: boolean;
  guidesMap: Record<string, TippData>;
  fetchGuides: () => Promise<void>;
  getGuideBySlug: (slug: string) => TippData | undefined;
};

export const useGuideState = create<GuideState>()((set, get) => ({
  hasLoaded: false,
  guidesMap: {},
  fetchGuides: async () => {
    if (get().hasLoaded) return;
    const data = await api
      .get(apiUrl(ApiEndpoints.guides_list))
      .catch((_error) => {
        console.error('Could not fetch guides');
      })
      .then((response) => response);
    if (!data) return;

    const guidesDictionary = Object.fromEntries(
      data?.data.map((itm: any) => [itm.slug, itm])
    );
    console.log('Fetched guides:', guidesDictionary);
    set({
      hasLoaded: true,
      guidesMap: guidesDictionary
    });
  },
  getGuideBySlug: (slug: string) => {
    get().fetchGuides();
    return get().guidesMap[slug];
  }
}));
