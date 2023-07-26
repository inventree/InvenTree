import { t } from '@lingui/macro';
import { Drawer, TextInput } from '@mantine/core';
import { Loader } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { IconBackspace, IconSearch } from '@tabler/icons-react';
import { useEffect, useState } from 'react';

/**
 * Construct a drawer which provides quick-search functionality
 * @param
 */
export function SearchDrawer({
  opened,
  onClose
}: {
  opened: boolean;
  onClose: () => void;
}) {
  const [value, setValue] = useState<string>('');
  const [searchText] = useDebouncedValue(value, 500);

  useEffect(() => {
    console.log(`Search text: ${searchText}`);
  }, [searchText]);

  return (
    <Drawer
      opened={opened}
      onClose={onClose}
      position="right"
      withCloseButton={false}
      styles={{ header: { width: '100%' }, title: { width: '100%' } }}
      title={
        <TextInput
          placeholder={t`Enter search text`}
          radius="xs"
          value={value}
          onChange={(event) => setValue(event.currentTarget.value)}
          icon={<IconSearch size="0.8rem" />}
          rightSection={
            value && <IconBackspace color="red" onClick={() => setValue('')} />
          }
          styles={{ root: { width: '100%' } }}
        />
      }
    >
      <Loader />
    </Drawer>
  );
}
