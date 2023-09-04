import { PartRenderer } from './PartRenderer';
import { StockItemRenderer } from './StockItemRenderer';

export enum RenderTypes {
  part = 'part',
  stockitem = 'stockitem'
}

// dict of renderers
const renderers = {
  [RenderTypes.stockitem]: StockItemRenderer,
  [RenderTypes.part]: PartRenderer
};

export interface RenderProps {
  type: RenderTypes;
  pk: string;
}

export function Render(props: RenderProps) {
  const { type, ...rest } = props;
  const RendererComponent = renderers[type];
  return <RendererComponent {...rest} />;
}
