import { Trans, t } from '@lingui/macro';
import { ActionIcon, Button, Group, TextInput } from '@mantine/core';
import { getHotkeyHandler, randomId } from '@mantine/hooks';
import { IconPlus } from '@tabler/icons-react';
import React from 'react';
import { useEffect, useState } from 'react';

import { ModelType } from '../../enums/ModelType';
import { IS_DEV_OR_DEMO } from '../../main';

// Scan Item
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

// Region input stuff
enum InputMethod {
  Manual = 'manually',
  ImageBarcode = 'imageBarcode'
}

interface inputProps {
  action: (items: ScanItem) => void;
}

export default function InputManual({ action }: inputProps) {
  const [value, setValue] = useState<string>('');

  const btnAddItem = () => {
    if (value === '') return;

    const newItem: ScanItem = {
      id: randomId(),
      ref: value,
      data: { item: value },
      timestamp: new Date(),
      source: InputMethod.Manual
    };
    action(newItem);
    setValue('');
  };

  const btnAddDummyItem = () => {
    const dummyItem: ScanItem = {
      id: randomId(),
      ref: 'Test item',
      data: {},
      timestamp: new Date(),
      source: InputMethod.Manual
    };
    action(dummyItem);
  };

  return (
    <>
      <Group>
        <TextInput
          placeholder={t`Enter item serial or data`}
          value={value}
          onChange={(event) => setValue(event.currentTarget.value)}
          onKeyDown={getHotkeyHandler([['Enter', btnAddItem]])}
        />
        <ActionIcon onClick={btnAddItem} w={16}>
          <IconPlus />
        </ActionIcon>
      </Group>

      {IS_DEV_OR_DEMO && (
        <Button onClick={btnAddDummyItem} variant="outline">
          <Trans>Add dummy item</Trans>
        </Button>
      )}
    </>
  );
}
