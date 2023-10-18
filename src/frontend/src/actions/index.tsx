import { ActionIcon, Group } from '@mantine/core';
import { IconQuestionMark } from '@tabler/icons-react';

import { RenderTypes } from '../components/renderers';
import { dummyDefaultActions } from './dummy';
import { purchase_orderActions } from './purchase_order';

export interface ActionFunctionType {
  barcode: string;
  data: any;
}

export interface ActionType {
  title: string;
  function: ({ barcode, data }: ActionFunctionType) => void;
  icon?: JSX.Element;
}

const actionsDict = {
  [RenderTypes.part]: dummyDefaultActions,
  [RenderTypes.stock_item]: dummyDefaultActions,
  [RenderTypes.stock_location]: dummyDefaultActions,
  [RenderTypes.supplier_part]: dummyDefaultActions,
  [RenderTypes.purchase_order]: purchase_orderActions,
  [RenderTypes.sales_order]: dummyDefaultActions,
  [RenderTypes.build_order]: dummyDefaultActions
};

interface ActionControlsProps extends ActionFunctionType {
  type: RenderTypes | undefined;
}

export function ActionControls({ type, barcode, data }: ActionControlsProps) {
  if (type === undefined) {
    return <Group></Group>;
  }

  const actions = actionsDict[type];
  return (
    <>
      <Group>
        {actions.map((action, idx) => (
          <ActionIcon
            onClick={() => action.function({ barcode, data })}
            title={action.title}
            key={idx}
          >
            {action.icon ? action.icon : <IconQuestionMark />}
          </ActionIcon>
        ))}
      </Group>
    </>
  );
}
