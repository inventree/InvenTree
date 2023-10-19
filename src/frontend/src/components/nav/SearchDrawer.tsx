import { Trans, t } from '@lingui/macro';
import {
  ActionIcon,
  Alert,
  Anchor,
  Center,
  Checkbox,
  Divider,
  Drawer,
  Group,
  Menu,
  Paper,
  Space,
  Stack,
  Text,
  TextInput
} from '@mantine/core';
import { Loader } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import {
  IconAlertCircle,
  IconBackspace,
  IconRefresh,
  IconSearch,
  IconSettings,
  IconX
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { ApiPaths, apiUrl } from '../../states/ApiState';
import { RenderInstance } from '../render/Instance';
import { ModelInformationDict, ModelType } from '../render/ModelType';

// Define type for handling individual search queries
type SearchQuery = {
  name: ModelType;
  enabled: boolean;
  parameters: any;
  results?: any;
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
      name: ModelType.part,
      parameters: {},
      enabled:
        permissionCheck('part.view') &&
        settingsCheck('SEARCH_PREVIEW_SHOW_PARTS')
    },
    {
      name: ModelType.supplierpart,
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
      name: ModelType.manufacturerpart,
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
      name: ModelType.partcategory,
      parameters: {},
      enabled:
        permissionCheck('part_category.view') &&
        settingsCheck('SEARCH_PREVIEW_SHOW_CATEGORIES')
    },
    {
      name: ModelType.stockitem,
      parameters: {
        part_detail: true,
        location_detail: true
      },
      enabled:
        permissionCheck('stock.view') &&
        settingsCheck('SEARCH_PREVIEW_SHOW_STOCK')
    },
    {
      name: ModelType.stocklocation,
      parameters: {},
      enabled:
        permissionCheck('stock_location.view') &&
        settingsCheck('SEARCH_PREVIEW_SHOW_LOCATIONS')
    },
    {
      name: ModelType.build,
      parameters: {
        part_detail: true
      },
      enabled:
        permissionCheck('build.view') &&
        settingsCheck('SEARCH_PREVIEW_SHOW_BUILD_ORDERS')
    },
    {
      name: ModelType.company,
      parameters: {},
      enabled:
        (permissionCheck('sales_order.view') ||
          permissionCheck('purchase_order.view')) &&
        settingsCheck('SEARCH_PREVIEW_SHOW_COMPANIES')
    },
    {
      name: ModelType.purchaseorder,
      parameters: {
        supplier_detail: true
      },
      enabled:
        permissionCheck('purchase_order.view') &&
        settingsCheck(`SEARCH_PREVIEW_SHOW_PURCHASE_ORDERS`)
    },
    {
      name: ModelType.salesorder,
      parameters: {
        customer_detail: true
      },
      enabled:
        permissionCheck('sales_order.view') &&
        settingsCheck(`SEARCH_PREVIEW_SHOW_SALES_ORDERS`)
    },
    {
      name: ModelType.returnorder,
      parameters: {
        customer_detail: true
      },
      enabled:
        permissionCheck('return_order.view') &&
        settingsCheck(`SEARCH_PREVIEW_SHOW_RETURN_ORDERS`)
    }
  ];
}

/*
 * Render the results for a single search query
 */
function QueryResultGroup({
  query,
  onRemove,
  onResultClick
}: {
  query: SearchQuery;
  onRemove: (query: ModelType) => void;
  onResultClick: (query: ModelType, pk: number) => void;
}) {
  if (query.results.count == 0) {
    return null;
  }

  const model = ModelInformationDict[query.name];
  return (
    <Paper shadow="sm" radius="xs" p="md">
      <Stack key={query.name}>
        <Group position="apart" noWrap={true}>
          <Group position="left" spacing={5} noWrap={true}>
            <Text size="lg">{model.label_multiple}</Text>
            <Text size="sm" italic>
              {' '}
              - {query.results.count} <Trans>results</Trans>
            </Text>
          </Group>
          <Space />
          <ActionIcon
            size="sm"
            color="red"
            variant="transparent"
            radius="xs"
            onClick={() => onRemove(query.name)}
          >
            <IconX />
          </ActionIcon>
        </Group>
        <Divider />
        <Stack>
          {query.results.results.map((result: any) => (
            <Anchor onClick={() => onResultClick(query.name, result.pk)}>
              <RenderInstance
                key={`${query.name}-${result.pk}`}
                instance={result}
                model={query.name}
              />
            </Anchor>
          ))}
        </Stack>
        <Space />
      </Stack>
    </Paper>
  );
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

  const [searchRegex, setSearchRegex] = useState<boolean>(false);
  const [searchWhole, setSearchWhole] = useState<boolean>(false);

  // Construct a list of search queries based on user permissions
  const searchQueries: SearchQuery[] = buildSearchQueries().filter(
    (q) => q.enabled
  );

  // Re-fetch data whenever the search term is updated
  useEffect(() => {
    // TODO: Implement search functionality
    searchQuery.refetch();
  }, [searchText]);

  // Function for performing the actual search query
  const performSearch = async () => {
    // Return empty result set if no search text
    if (!searchText) {
      return [];
    }

    let params: any = {
      offset: 0,
      limit: 10, // TODO: Make this configurable (based on settings)
      search: searchText,
      search_regex: searchRegex,
      search_whole: searchWhole
    };

    // Add in custom query parameters
    searchQueries.forEach((query) => {
      params[query.name] = query.parameters;
    });

    return api
      .post(apiUrl(ApiPaths.api_search), params)
      .then(function (response) {
        return response.data;
      })
      .catch(function (error) {
        console.error(error);
        return [];
      });
  };

  // Search query manager
  const searchQuery = useQuery({
    queryKey: ['search', searchText, searchRegex, searchWhole],
    queryFn: performSearch,
    refetchOnWindowFocus: false
  });

  // A list of queries which return valid results
  const [queryResults, setQueryResults] = useState<SearchQuery[]>([]);

  // Update query results whenever the search results change
  useEffect(() => {
    if (searchQuery.data) {
      let queries = searchQueries.filter(
        (query) => query.name in searchQuery.data
      );

      for (let key in searchQuery.data) {
        let query = queries.find((q) => q.name == key);
        if (query) {
          query.results = searchQuery.data[key];
        }
      }

      // Filter for results with non-zero count
      queries = queries.filter((query) => query.results.count > 0);

      setQueryResults(queries);
    } else {
      setQueryResults([]);
    }
  }, [searchQuery.data]);

  // Callback to remove a set of results from the list
  function removeResults(query: ModelType) {
    setQueryResults(queryResults.filter((q) => q.name != query));
  }

  // Callback when the drawer is closed
  function closeDrawer() {
    setValue('');
    onClose();
  }

  const navigate = useNavigate();

  // Callback when one of the search results is clicked
  function onResultClick(query: ModelType, pk: number) {
    closeDrawer();
    navigate(
      ModelInformationDict[query].url_detail.replace(':pk', pk.toString())
    );
  }

  return (
    <Drawer
      opened={opened}
      size="md"
      onClose={closeDrawer}
      position="right"
      withCloseButton={false}
      styles={{ header: { width: '100%' }, title: { width: '100%' } }}
      title={
        <Group position="apart" spacing={1} noWrap={true}>
          <TextInput
            placeholder={t`Enter search text`}
            radius="xs"
            value={value}
            onChange={(event) => setValue(event.currentTarget.value)}
            icon={<IconSearch size="0.8rem" />}
            rightSection={
              value && (
                <IconBackspace color="red" onClick={() => setValue('')} />
              )
            }
            styles={{ root: { width: '100%' } }}
          />
          <ActionIcon
            size="lg"
            variant="outline"
            radius="xs"
            onClick={() => searchQuery.refetch()}
          >
            <IconRefresh />
          </ActionIcon>
          <Menu>
            <Menu.Target>
              <ActionIcon size="lg" variant="outline" radius="xs">
                <IconSettings />
              </ActionIcon>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Label>{t`Search Options`}</Menu.Label>
              <Menu.Item>
                <Checkbox
                  label={t`Regex search`}
                  checked={searchRegex}
                  onChange={(event) =>
                    setSearchRegex(event.currentTarget.checked)
                  }
                  radius="sm"
                />
              </Menu.Item>
              <Menu.Item>
                <Checkbox
                  label={t`Whole word search`}
                  checked={searchWhole}
                  onChange={(event) =>
                    setSearchWhole(event.currentTarget.checked)
                  }
                  radius="sm"
                />
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      }
    >
      {searchQuery.isFetching && (
        <Center>
          <Loader />
        </Center>
      )}
      {!searchQuery.isFetching && !searchQuery.isError && (
        <Stack spacing="md">
          {queryResults.map((query) => (
            <QueryResultGroup
              query={query}
              onRemove={(query) => removeResults(query)}
              onResultClick={(query, pk) => onResultClick(query, pk)}
            />
          ))}
        </Stack>
      )}
      {searchQuery.isError && (
        <Alert
          color="red"
          radius="sm"
          variant="light"
          title={t`Error`}
          icon={<IconAlertCircle size="1rem" />}
        >
          <Trans>An error occurred during search query</Trans>
        </Alert>
      )}
      {searchText &&
        !searchQuery.isFetching &&
        !searchQuery.isError &&
        queryResults.length == 0 && (
          <Alert
            color="blue"
            radius="sm"
            variant="light"
            title={t`No results`}
            icon={<IconSearch size="1rem" />}
          >
            <Trans>No results available for search query</Trans>
          </Alert>
        )}
    </Drawer>
  );
}
