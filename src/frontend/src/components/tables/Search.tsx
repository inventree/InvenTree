import { CloseButton, TextInput } from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';
import { useState } from 'react';

export function TableSearchInput({
  searchCallback
}: {
  searchCallback: (searchTerm: string) => void;
}) {
  const [value, setValue] = useState<string>('');

  // Debounce timer
  let timer: any = null;

  // Handle search input change
  function handleSearch(event: any) {
    const value = event.target.value;

    setValue(value);

    clearTimeout(timer);

    timer = setTimeout(() => {
      searchCallback(value);
    }, 500);
  }

  // Clear search term
  function clearSearch() {
    setValue('');
    searchCallback('');
    clearTimeout(timer);
  }

  return (
    <TextInput
      value={value}
      icon={<IconSearch />}
      placeholder="Search"
      onChange={handleSearch}
      rightSection={
        value.length > 0 ? (
          <CloseButton size="xs" onClick={clearSearch} />
        ) : null
      }
    />
  );
}
