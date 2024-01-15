import { Trans, t } from '@lingui/macro';
import { Badge, Group, Table, Tooltip } from '@mantine/core';
import {
  IconCopy,
  IconCornerUpRightDouble,
  IconCurrencyDollar,
  IconGridDots,
  IconShoppingCartFilled,
  IconTool,
  IconWorldCode
} from '@tabler/icons-react';
import React from 'react';

const left = [
  {
    field: 'Description',
    value: 'Hello there'
  },
  {
    field: 'Potato',
    value: 'Tomato'
  }
];

export type PartIconsType = {
  assembly: boolean;
  template: boolean;
  component: boolean;
  trackable: boolean;
  purchaseable: boolean;
  saleable: boolean;
  virtual: boolean;
};

function PartIcons({
  assembly,
  template,
  component,
  trackable,
  purchaseable,
  saleable,
  virtual
}: PartIconsType) {
  return (
    <td colSpan={2}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {template && (
          <Tooltip
            label={t`Part is a template part (variants can be made from this part)`}
          >
            <IconCopy />
          </Tooltip>
        )}
        {assembly && (
          <Tooltip label={t`Part can be assembled from other parts`}>
            <IconTool />
          </Tooltip>
        )}
        {component && (
          <Tooltip label={t`Part can be used in assemblies`}>
            <IconGridDots />
          </Tooltip>
        )}
        {trackable && (
          <Tooltip label={t`Part stock is tracked by serial number`}>
            <IconCornerUpRightDouble />
          </Tooltip>
        )}
        {purchaseable && (
          <Tooltip label={t`Part can be purchased from external suppliers`}>
            <IconShoppingCartFilled />
          </Tooltip>
        )}
        {saleable && (
          <Tooltip label={t`Part can be sold to customers`}>
            <IconCurrencyDollar />
          </Tooltip>
        )}
        {virtual && (
          <Tooltip label={t`Part is virtual (not a physical part)`}>
            <Badge color="yellow" variant="filled">
              <div
                style={{ display: 'flex', alignItems: 'center', gap: '5px' }}
              >
                <IconWorldCode size={17} /> <Trans>Virtual</Trans>
              </div>
            </Badge>
          </Tooltip>
        )}
      </div>
    </td>
  );
}

export function DetailsTable(part: any) {
  console.log(part.part);
  return (
    <Group>
      <Table striped>
        <tbody>
          <tr>
            <PartIcons
              assembly={part.part.assembly}
              template={part.part.is_template}
              component={part.part.component}
              trackable={part.part.trackable}
              purchaseable={part.part.purchaseable}
              saleable={part.part.salable}
              virtual={part.part.virtual}
            />
          </tr>
          <tr>
            <td>{left[0].field}</td>
            <td>{left[0].value}</td>
          </tr>
          <tr>
            <td>{left[1].field}</td>
            <td>{left[1].value}</td>
          </tr>
        </tbody>
      </Table>
    </Group>
  );
}
