import type { InstanceRenderInterface } from '@lib/types/Rendering';
import type { ReactNode } from 'react';

export type setRenderProps = (
  model: string,
  renderer: (props: Readonly<InstanceRenderInterface>) => ReactNode
) => void;
