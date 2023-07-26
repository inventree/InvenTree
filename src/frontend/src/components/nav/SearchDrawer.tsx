import { t } from '@lingui/macro';
import { Drawer, TextInput } from '@mantine/core';
import { Loader } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { IconBackspace, IconSearch } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { api } from '../../App';

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
    // TODO: Implement search functionality
    refetch();
  }, [searchText]);

  // Function for performing the actual search query
  const performSearch = async () => {
    console.log('Performing search:', searchText);
    // Return empty result set if no search text
    if (!searchText) {
      return [];
    }

    let params: any = {
      offset: 0,
      limit: 10,
      search: searchText,
      searchRegex: false, // TODO: Make this configurable
      searchWhole: false // TODO: Make this configurable
    };

    // TODO: Implement specific search functionality based on user settings (and permissions)
    params.part = {};
    params.supplierpart = {};
    params.manufacturerpart = {};
    params.partcategory = {};
    params.stock = {};
    params.stocklocation = {};
    params.build = {};
    params.company = {};
    params.purchaseorder = {};
    params.salesorder = {};
    params.returnorder = {};

    return api
      .post(`/search/`, params)
      .then(function (response) {
        console.log('results:', response);
        return response.data;
      })
      .catch(function (error) {
        console.error(error);
        return [];
      });
  };

  // Search query manager
  const { data, isError, isFetching, isLoading, refetch } = useQuery(
    ['search', searchText],
    performSearch,
    {}
  );

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
          icon={<IconSearch size="0.8rem" onClick={() => refetch()} />}
          rightSection={
            value && <IconBackspace color="red" onClick={() => setValue('')} />
          }
          styles={{ root: { width: '100%' } }}
        />
      }
    >
      {isFetching && <Loader />}
    </Drawer>
  );
}
