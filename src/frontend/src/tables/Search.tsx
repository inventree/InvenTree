import { t } from '@lingui/macro';
import { CloseButton, TextInput } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { IconSearch } from '@tabler/icons-react';
import { useEffect, useState } from 'react';

export function TableSearchInput({
  searchCallback
}: {
  searchCallback: (searchTerm: string) => void;
}) {
  const [value, setValue] = useState<string>('');
  const [searchText] = useDebouncedValue(value, 500);

  useEffect(() => {
    searchCallback(searchText);
  }, [searchText]);

  return (
    <TextInput
      value={value}
      icon={<IconSearch />}
      placeholder={t`Search`}
      onChange={(event) => setValue(event.target.value)}
      rightSection={
        value.length > 0 ? (
          <CloseButton size="xs" onClick={() => setValue('')} />
        ) : null
      }
    />
  );
}
