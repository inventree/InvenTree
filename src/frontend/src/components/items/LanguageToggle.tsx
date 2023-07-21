import { ActionIcon, Group, Select } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconLanguage } from '@tabler/icons-react';
import { useEffect, useState } from 'react';

import { Locales, languages } from '../../contexts/LanguageContext';
import { useLocalState } from '../../states/LocalState';

export function LanguageToggle() {
  const [open, toggle] = useDisclosure();
  const [value, setValue] = useState<string | null>(null);
  const [locale, setLanguage] = useLocalState((state) => [
    state.language,
    state.setLanguage
  ]);

  // change global language on change
  useEffect(() => {
    if (value === null) return;
    setLanguage(value as Locales);
  }, [value]);

  // set language on component load
  useEffect(() => {
    setValue(locale);
  }, [locale]);

  return (
    <Group
      position="center"
      style={{
        border: open === true ? `1px dashed ` : ``,
        margin: open === true ? 2 : 12,
        padding: open === true ? 8 : 0
      }}
    >
      <ActionIcon onClick={() => toggle.toggle()} size="lg">
        <IconLanguage />
      </ActionIcon>
      {open && (
        <Group>
          <Select w={80} data={languages} value={value} onChange={setValue} />
        </Group>
      )}
    </Group>
  );
}
