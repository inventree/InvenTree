import { Trans, t } from '@lingui/macro';
import {
  Anchor,
  Badge,
  Group,
  Skeleton,
  Table,
  Text,
  Tooltip
} from '@mantine/core';
import {
  IconCopy,
  IconCornerUpRightDouble,
  IconCurrencyDollar,
  IconGridDots,
  IconShoppingCartFilled,
  IconTool,
  IconWorldCode
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { privateEncrypt } from 'crypto';
import React, { Suspense, useEffect, useState } from 'react';

import { api } from '../../App';
import { GetIcon, InvenTreeIcon } from '../../functions/icons';
import { useInstance } from '../../hooks/UseInstance';
import { apiUrl } from '../../states/ApiState';

export type PartIconsType = {
  assembly: boolean;
  template: boolean;
  component: boolean;
  trackable: boolean;
  purchaseable: boolean;
  saleable: boolean;
  virtual: boolean;
  active: boolean;
};

function PartIcon(icon: string) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
      <InvenTreeIcon icon={icon} />
    </div>
  );
}

function PartIcons({
  assembly,
  template,
  component,
  trackable,
  purchaseable,
  saleable,
  virtual,
  active
}: PartIconsType) {
  return (
    <td colSpan={2}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {!active && (
          <Tooltip label="Part is not active">
            <Badge color="red" variant="filled">
              <div
                style={{ display: 'flex', alignItems: 'center', gap: '5px' }}
              >
                <InvenTreeIcon icon="inactive" iconProps={{ size: 19 }} />{' '}
                <Trans>Inactive</Trans>
              </div>
            </Badge>
          </Tooltip>
        )}
        {template && (
          <Tooltip
            label={t`Part is a template part (variants can be made from this part)`}
            children={PartIcon('template')}
          />
        )}
        {assembly && (
          <Tooltip
            label={t`Part can be assembled from other parts`}
            children={PartIcon('assembly')}
          />
        )}
        {component && (
          <Tooltip
            label={t`Part can be used in assemblies`}
            children={PartIcon('component')}
          />
        )}
        {trackable && (
          <Tooltip
            label={t`Part stock is tracked by serial number`}
            children={PartIcon('trackable')}
          />
        )}
        {purchaseable && (
          <Tooltip
            label={t`Part can be purchased from external suppliers`}
            children={PartIcon('purchaseable')}
          />
        )}
        {saleable && (
          <Tooltip
            label={t`Part can be sold to customers`}
            children={PartIcon('saleable')}
          />
        )}
        {virtual && (
          <Tooltip label={t`Part is virtual (not a physical part)`}>
            <Badge color="yellow" variant="filled">
              <div
                style={{ display: 'flex', alignItems: 'center', gap: '5px' }}
              >
                <InvenTreeIcon icon="virtual" iconProps={{ size: 18 }} />{' '}
                <Trans>Virtual</Trans>
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
  console.log('FF', field_data, field_value);

  return (
    <tr>
      <td style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
        <InvenTreeIcon icon={field_data.name} />
        <Text>{field_data.label}</Text>
      </td>
      <td>
        {field_value ? field_value : field_data.unit && '0'}{' '}
        {field_data.unit == true && unit}
      </td>
    </tr>
  );
}

function TableLinkField({
  field_data,
  field_value,
  pk
}: {
  field_data: any;
  field_value: any;
  pk: string;
}) {
  const {
    instance: variant,
    refreshInstance,
    instanceQuery
  } = useInstance({
    endpoint: field_data.path,
    pk: field_value
  });

  const link = (
    <Anchor
      href={'/platform' + field_data.dest + field_value}
      target={field_data.external ? '_blank' : undefined}
      rel={field_data.external ? 'noreferrer noopener' : undefined}
    >
      <Suspense fallback={<Skeleton width={60} />}>
        {!instanceQuery.isFetching ? (
          <Text>{variant.full_name}</Text>
        ) : (
          <Skeleton width={200} height={20} radius="xl" />
        )}
      </Suspense>
    </Anchor>
  );

  return <TableStringField field_data={field_data} field_value={link} />;
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
  console.log(part);
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
                active={part.active}
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
                  unit={part.units}
                />
              );
            } else if (data.type == 'link') {
              return (
                <TableLinkField
                  field_data={data}
                  field_value={part[data.name]}
                  key={index}
                  pk={part.pk}
                />
              );
            }
          })}
        </tbody>
      </Table>
    </Group>
  );
}
