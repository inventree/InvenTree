import { t } from '@lingui/macro';
import { Drawer, TextInput } from '@mantine/core';
import { Loader } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import {
  IconBackspace,
  IconSearch,
  IconSettingsCheck
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { api } from '../../App';

type SearchQuery = {
  name: string;
  title: string;
  enabled: boolean;
  parameters: any;
};

// Placeholder function for permissions checks (will be replaced with a proper implementation)
function permissionCheck(permission: string) {
  return true;
}

// Placeholder function for settings checks (will be replaced with a proper implementation)
function settingsCheck(setting: string) {
  return true;
}

/*
 * Build a list of search queries based on user permissions
 */
function buildSearchQueries(): SearchQuery[] {
  return [
    {
      name: 'part',
      title: t`Parts`,
      parameters: {},
      enabled:
        permissionCheck('part.view') &&
        settingsCheck('SEARCH_PREVIEW_SHOW_PARTS')
    },
    {
      name: 'supplierpart',
      title: t`Supplier Parts`,
      parameters: {
        part_detail: true,
        supplier_detail: true,
        manufacturer_detail: true
      },
      enabled:
        permissionCheck('part.view') &&
        permissionCheck('purchase_order.view') &&
        settingsCheck('SEARCH_PREVIEW_SHOW_SUPPLIER_PARTS')
    },
    {
      name: 'manufacturerpart',
      title: t`Manufacturer Parts`,
      parameters: {
        part_detail: true,
        supplier_detail: true,
        manufacturer_detail: true
      },
      enabled:
        permissionCheck('part.view') &&
        permissionCheck('purchase_order.view') &&
        settingsCheck('SEARCH_PREVIEW_SHOW_MANUFACTURER_PARTS')
    },
    {
      name: 'partcategory',
      title: t`Part Categories`,
      parameters: {},
      enabled:
        permissionCheck('part_category.view') &&
        settingsCheck('SEARCH_PREVIEW_SHOW_CATEGORIES')
    },
    {
      name: 'stock',
      title: t`Stock Items`,
      parameters: {
        part_detail: true,
        location_detail: true
      },
      enabled:
        permissionCheck('stock.view') &&
        settingsCheck('SEARCH_PREVIEW_SHOW_STOCK')
    }

    // TODO: stock locations
    // TODO: build orders
    // TODO: Purchase orders
    // TODO: sales orders
    // TODO: return orders
  ];
}

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

  // Construct a list of search queries based on user permissions
  const searchQueries: SearchQuery[] = buildSearchQueries().filter(
    (q) => q.enabled
  );

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

    // Add in custom query parameters
    searchQueries.forEach((query) => {
      params[query.name] = query.parameters;
    });

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
