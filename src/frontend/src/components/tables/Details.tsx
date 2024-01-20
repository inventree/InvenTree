import { Trans, t } from '@lingui/macro';
import { Badge, Group, Table, Text, Tooltip } from '@mantine/core';
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

import { GetIcon } from '../../functions/icons';

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

function TableStringField({
  field_data,
  field_value,
  unit = null
}: {
  field_data: any;
  field_value: any;
  unit?: null | string;
}) {
  console.log(field_data, field_value);
  return (
    <tr>
      <td style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
        {GetIcon(field_data.name)}
        <Text>{field_data.label}</Text>
      </td>
      <td>
        {field_value} {unit && unit.length > 0 ? unit : 'meters'}
      </td>
    </tr>
  );
}

export function DetailsTable({
  part,
  fields,
  partIcons = false
}: {
  part: any;
  fields: any;
  partIcons?: boolean;
}) {
  console.log('DetailsTable', part, fields);
  return (
    <Group>
      <Table striped>
        <tbody>
          {partIcons && (
            <tr>
              <PartIcons
                assembly={part.assembly}
                template={part.is_template}
                component={part.component}
                trackable={part.trackable}
                purchaseable={part.purchaseable}
                saleable={part.salable}
                virtual={part.virtual}
              />
            </tr>
          )}
          {fields.map((data: any, index: number) => {
            console.log('Mapping', data);
            if (data.type == 'string' || data.type == 'text') {
              return (
                <TableStringField
                  field_data={data}
                  field_value={part[data.name]}
                  key={index}
                  unit={data.unit ?? part['units']}
                />
              );
            }
          })}
        </tbody>
      </Table>
    </Group>
  );
}
