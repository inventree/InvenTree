import { Loader } from '@mantine/core';
import { useMemo, useState } from 'react';

import type { ModelType } from '../../enums/ModelType';
import { useApi } from '../../hooks/UseApi';
import { RenderInstance } from './Instance';

/**
 * Render a model instance from a URL
 * @param model Model type
 * @param url URL to fetch instance from
 * @returns JSX Element
 */
export function InstanceFromUrl({
  model,
  url
}: Readonly<{
  model: ModelType;
  url: string;
}>) {
  const api = useApi();
  const [data, setData] = useState<any>(null);
  useMemo(
    () =>
      api.get(url).then((res) => {
        setData(res.data);
      }),
    [model, url]
  );

  if (!data) return <Loader />;

  return <RenderInstance instance={data} model={model} />;
}
