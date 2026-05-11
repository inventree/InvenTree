import type { ReactNode } from 'react';
import type { InstanceRenderInterface } from '../types/Rendering';

export type setRenderProps = (
  model: string,
  renderer: (props: Readonly<InstanceRenderInterface>) => ReactNode
) => void;
