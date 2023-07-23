import { CloseButton, TextInput } from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';
import { useEffect, useState } from 'react';

export function TableSearchInput({
  searchCallback
}: {
  searchCallback: (searchTerm: string) => void;
}) {
  const [value, setValue] = useState<string>('');
  const [searchValue, setSearchValue] = useState<string>('');

  useEffect(() => {
    const timer = setTimeout(() => {
      if (value != searchValue) {
        setSearchValue(value);
        searchCallback(value);
      }
    }, 500);
    return () => clearTimeout(timer);
  });

  return (
    <TextInput
      value={value}
      icon={<IconSearch />}
      placeholder="Search"
      onChange={(event) => setValue(event.target.value)}
      rightSection={
        value.length > 0 ? (
          <CloseButton size="xs" onClick={(event) => setValue('')} />
        ) : null
      }
    />
  );
}
