import { ActionIcon, Group } from '@mantine/core';
import { IconQuestionMark } from '@tabler/icons-react';

import { ModelType } from '../enums/ModelType';
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

const actionsDict: { [id: string]: ActionType[] } = {
  [ModelType.part]: dummyDefaultActions,
  [ModelType.stockitem]: dummyDefaultActions,
  [ModelType.stocklocation]: dummyDefaultActions,
  [ModelType.supplierpart]: dummyDefaultActions,
  [ModelType.purchaseorder]: purchase_orderActions,
  [ModelType.salesorder]: dummyDefaultActions,
  [ModelType.build]: dummyDefaultActions
};

interface ActionControlsProps extends ActionFunctionType {
  type: ModelType | undefined;
}

export function ActionControls({ type, barcode, data }: ActionControlsProps) {
  if (type === undefined) {
    return <Group></Group>;
  }

  const actions = actionsDict[type] || dummyDefaultActions;
  return (
    <>
      <Group>
        {actions.map((action: any, idx: any) => (
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
