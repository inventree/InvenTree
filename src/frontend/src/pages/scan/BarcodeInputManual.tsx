import { t } from '@lingui/macro';
import { ActionIcon, Group, TextInput } from '@mantine/core';
import { getHotkeyHandler, randomId } from '@mantine/hooks';
import { IconPlus } from '@tabler/icons-react';
import { useState } from 'react';

import { ModelType } from '../../enums/ModelType';

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
    </>
  );
}
