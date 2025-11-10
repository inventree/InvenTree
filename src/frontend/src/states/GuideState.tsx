import { create } from 'zustand';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { TippData } from '@lib/types/Core';
import { api } from '../App';

type GuideState = {
  hasLoaded: boolean;
  guidesMap: Record<string, TippData>;
  fetchGuides: () => Promise<void>;
  getGuideBySlug: (slug: string) => any | undefined;
  closeGuide: (slug: string) => void;
};

export const useGuideState = create<GuideState>()((set, get) => ({
  hasLoaded: false,
  guidesMap: {},
  fetchGuides: async () => {
    if (get().hasLoaded) return;
    const data = await api
      .get(`${apiUrl(ApiEndpoints.guides_list)}?guide_data=true`)
      .catch((_error) => {
        console.error('Could not fetch guides');
      })
      .then((response) => response);
    if (!data) return;

    const guidesDictionary = Object.fromEntries(
      data?.data.map((itm: any) => [itm.slug, itm])
    );
    set({
      hasLoaded: true,
      guidesMap: guidesDictionary
    });
  },
  getGuideBySlug: (slug: string) => {
    get().fetchGuides();
    return get().guidesMap[slug];
  },
  closeGuide: async (slug) => {
    const guides = get().guidesMap;
    await api
      .post(apiUrl(ApiEndpoints.guide_dismiss, slug))
      .then(() => {})
      .catch((err) => {
        console.error(`Could not dismiss guide ${slug} with error: ${err}`);
      });

    delete guides[slug];
    set({ guidesMap: { ...guides } });
  }
}));
