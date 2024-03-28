import { Trans } from '@lingui/macro';
import { Checkbox, ScrollArea, Table, Text, rem } from '@mantine/core';
import React from 'react';

import { RenderInstance } from '../../components/render/Instance';
import { ModelType } from '../../enums/ModelType';

interface ScanItem {
  id: string;
  ref: string;
  data: any;
  instance?: any;
  timestamp: Date;
  source: string;
  link?: string;
  model?: ModelType;
  pk?: string;
}

export interface HistoryTableProps {
  data: ScanItem[];
  selection: string[];
  setSelection: React.Dispatch<React.SetStateAction<string[]>>;
}

export default function HistoryTable({
  data,
  selection,
  setSelection
}: HistoryTableProps) {
  const toggleRow = (id: string) =>
    setSelection((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id]
    );
  const toggleAll = () =>
    setSelection((current) =>
      current.length === data.length ? [] : data.map((item) => item.id)
    );

  const rows = data.map((item) => {
    const selected = selection.includes(item.id);
    return (
      <tr key={item.id}>
        <td>
          <Checkbox
            checked={selection.includes(item.id)}
            onChange={() => toggleRow(item.id)}
            transitionDuration={0}
          />
        </td>
        <td>
          {item.pk && item.model && item.instance ? (
            <RenderInstance model={item.model} instance={item.instance} />
          ) : (
            item.ref
          )}
        </td>
        <td>{item.model}</td>
        <td>{item.source}</td>
        <td>{item.timestamp?.toString()}</td>
      </tr>
    );
  });

  // Rendering
  return (
    <ScrollArea>
      {data.length === 0 ? (
        <Text>
          <Trans>No history</Trans>
        </Text>
      ) : (
        <Table miw={800} verticalSpacing="sm">
          <thead>
            <tr>
              <th style={{ width: rem(40) }}>
                <Checkbox
                  onChange={toggleAll}
                  checked={selection.length === data.length}
                  indeterminate={
                    selection.length > 0 && selection.length !== data.length
                  }
                  transitionDuration={0}
                />
              </th>
              <th>
                <Trans>Item</Trans>
              </th>
              <th>
                <Trans>Type</Trans>
              </th>
              <th>
                <Trans>Source</Trans>
              </th>
              <th>
                <Trans>Scanned at</Trans>
              </th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </Table>
      )}
    </ScrollArea>
  );
}
