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
  Loader,
  Menu,
  Paper,
  Space,
  Stack,
  Text,
  TextInput,
  Tooltip
} from '@mantine/core';
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
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { navigateToLink } from '../../functions/navigation';
import { apiUrl } from '../../states/ApiState';
import { useUserSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';
import { Boundary } from '../Boundary';
import { RenderInstance } from '../render/Instance';
import { ModelInformationDict, getModelInfo } from '../render/ModelType';

// Define type for handling individual search queries
type SearchQuery = {
  model: ModelType;
  enabled: boolean;
  parameters: any;
  results?: any;
};

/*
 * Render the results for a single search query
 */
function QueryResultGroup({
  query,
  onRemove,
  onResultClick
}: Readonly<{
  query: SearchQuery;
  onRemove: (query: ModelType) => void;
  onResultClick: (query: ModelType, pk: number, event: any) => void;
}>) {
  if (query.results.count == 0) {
    return null;
  }

  const model = getModelInfo(query.model);

  return (
    <Paper
      withBorder
      shadow='sm'
      p='md'
      key={`paper-${query.model}`}
      aria-label={`search-group-${query.model}`}
    >
      <Stack key={`stack-${query.model}`}>
        <Group justify='space-between' wrap='nowrap'>
          <Group justify='left' gap={5} wrap='nowrap'>
            <Text size='lg'>{model.label_multiple}</Text>
            <Text size='sm' style={{ fontStyle: 'italic' }}>
              {' '}
              - {query.results.count} <Trans>results</Trans>
            </Text>
          </Group>
          <Space />
          <ActionIcon
            size='sm'
            color='red'
            variant='transparent'
            radius='xs'
            aria-label={`remove-search-group-${query.model}`}
            onClick={() => onRemove(query.model)}
          >
            <IconX />
          </ActionIcon>
        </Group>
        <Divider />
        <Stack aria-label={`search-group-results-${query.model}`}>
          {query.results.results.map((result: any) => (
            <Anchor
              underline='never'
              onClick={(event: any) =>
                onResultClick(query.model, result.pk, event)
              }
              key={`result-${query.model}-${result.pk}`}
            >
              <RenderInstance instance={result} model={query.model} />
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
}: Readonly<{
  opened: boolean;
  onClose: () => void;
}>) {
  const [value, setValue] = useState<string>('');
  const [searchText] = useDebouncedValue(value, 500);

  const [searchRegex, setSearchRegex] = useState<boolean>(false);
  const [searchWhole, setSearchWhole] = useState<boolean>(false);

  const user = useUserState();
  const userSettings = useUserSettingsState();

  // Build out search queries based on user permissions and preferences
  const searchQueryList: SearchQuery[] = useMemo(() => {
    return [
      {
        model: ModelType.part,
        parameters: {
          active: userSettings.isSet('SEARCH_HIDE_INACTIVE_PARTS')
            ? true
            : undefined
        },
        enabled:
          user.hasViewRole(UserRoles.part) &&
          userSettings.isSet('SEARCH_PREVIEW_SHOW_PARTS')
      },
      {
        model: ModelType.supplierpart,
        parameters: {
          part_detail: true,
          supplier_detail: true,
          manufacturer_detail: true
        },
        enabled:
          user.hasViewRole(UserRoles.part) &&
          user.hasViewRole(UserRoles.purchase_order) &&
          userSettings.isSet('SEARCH_PREVIEW_SHOW_SUPPLIER_PARTS')
      },
      {
        model: ModelType.manufacturerpart,
        parameters: {
          part_detail: true,
          supplier_detail: true,
          manufacturer_detail: true
        },
        enabled:
          user.hasViewRole(UserRoles.part) &&
          user.hasViewRole(UserRoles.purchase_order) &&
          userSettings.isSet('SEARCH_PREVIEW_SHOW_MANUFACTURER_PARTS')
      },
      {
        model: ModelType.partcategory,
        parameters: {},
        enabled:
          user.hasViewRole(UserRoles.part_category) &&
          userSettings.isSet('SEARCH_PREVIEW_SHOW_CATEGORIES')
      },
      {
        model: ModelType.stockitem,
        parameters: {
          part_detail: true,
          location_detail: true,
          in_stock: userSettings.isSet('SEARCH_PREVIEW_HIDE_UNAVAILABLE_STOCK')
            ? true
            : undefined
        },
        enabled:
          user.hasViewRole(UserRoles.stock) &&
          userSettings.isSet('SEARCH_PREVIEW_SHOW_STOCK')
      },
      {
        model: ModelType.stocklocation,
        parameters: {},
        enabled:
          user.hasViewRole(UserRoles.stock_location) &&
          userSettings.isSet('SEARCH_PREVIEW_SHOW_LOCATIONS')
      },
      {
        model: ModelType.build,
        parameters: {
          part_detail: true
        },
        enabled:
          user.hasViewRole(UserRoles.build) &&
          userSettings.isSet('SEARCH_PREVIEW_SHOW_BUILD_ORDERS')
      },
      {
        model: ModelType.company,
        parameters: {},
        enabled:
          (user.hasViewRole(UserRoles.sales_order) ||
            user.hasViewRole(UserRoles.purchase_order)) &&
          userSettings.isSet('SEARCH_PREVIEW_SHOW_COMPANIES')
      },
      {
        model: ModelType.purchaseorder,
        parameters: {
          supplier_detail: true,
          outstanding: userSettings.isSet(
            'SEARCH_PREVIEW_EXCLUDE_INACTIVE_PURCHASE_ORDERS'
          )
            ? true
            : undefined
        },
        enabled:
          user.hasViewRole(UserRoles.purchase_order) &&
          userSettings.isSet('SEARCH_PREVIEW_SHOW_PURCHASE_ORDERS')
      },
      {
        model: ModelType.salesorder,
        parameters: {
          customer_detail: true,
          outstanding: userSettings.isSet(
            'SEARCH_PREVIEW_EXCLUDE_INACTIVE_SALES_ORDERS'
          )
            ? true
            : undefined
        },
        enabled:
          user.hasViewRole(UserRoles.sales_order) &&
          userSettings.isSet('SEARCH_PREVIEW_SHOW_SALES_ORDERS')
      },
      {
        model: ModelType.returnorder,
        parameters: {
          customer_detail: true,
          outstanding: userSettings.isSet(
            'SEARCH_PREVIEW_EXCLUDE_INACTIVE_RETURN_ORDERS'
          )
            ? true
            : undefined
        },
        enabled:
          user.hasViewRole(UserRoles.return_order) &&
          userSettings.isSet('SEARCH_PREVIEW_SHOW_RETURN_ORDERS')
      }
    ];
  }, [user, userSettings]);

  // Construct a list of search queries based on user permissions
  const searchQueries: SearchQuery[] = searchQueryList.filter((q) => q.enabled);

  // Re-fetch data whenever the search term is updated
  useEffect(() => {
    searchQuery.refetch();
  }, [searchText]);

  // Function for performing the actual search query
  const performSearch = async () => {
    // Return empty result set if no search text
    if (!searchText) {
      return [];
    }

    const params: any = {
      offset: 0,
      limit: userSettings.getSetting('SEARCH_PREVIEW_RESULTS', '10'),
      search: searchText,
      search_regex: searchRegex,
      search_whole: searchWhole
    };

    // Add in custom query parameters
    searchQueries.forEach((query) => {
      params[query.model] = query.parameters;
    });

    return api
      .post(apiUrl(ApiEndpoints.api_search), params)
      .then((response) => response.data)
      .catch((error) => {
        console.error(error);
        return [];
      });
  };

  // Search query manager
  const searchQuery = useQuery({
    queryKey: ['search', searchText, searchRegex, searchWhole],
    queryFn: performSearch
  });

  // A list of queries which return valid results
  const [queryResults, setQueryResults] = useState<SearchQuery[]>([]);

  // Update query results whenever the search results change
  useEffect(() => {
    if (searchQuery.data) {
      let queries = searchQueries.filter(
        (query) => query.model in searchQuery.data
      );

      for (const key in searchQuery.data) {
        const query = queries.find((q) => q.model == key);
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
    setQueryResults(queryResults.filter((q) => q.model != query));
  }

  // Callback when the drawer is closed
  function closeDrawer() {
    setValue('');
    onClose();
  }

  const navigate = useNavigate();

  // Callback when one of the search results is clicked
  function onResultClick(query: ModelType, pk: number, event: any) {
    const targetModel = ModelInformationDict[query];
    if (targetModel.url_detail == undefined) {
      return;
    }

    if (event?.ctrlKey || event?.shiftKey) {
      // Keep the drawer open in this condition
    } else {
      closeDrawer();
    }

    const url = targetModel.url_detail.replace(':pk', pk.toString());
    navigateToLink(url, navigate, event);
  }

  return (
    <Drawer
      opened={opened}
      size='xl'
      onClose={closeDrawer}
      position='right'
      withCloseButton={false}
      styles={{ header: { width: '100%' }, title: { width: '100%' } }}
      title={
        <Group justify='space-between' gap={1} wrap='nowrap'>
          <TextInput
            aria-label='global-search-input'
            placeholder={t`Enter search text`}
            value={value}
            onChange={(event) => setValue(event.currentTarget.value)}
            leftSection={<IconSearch size='0.8rem' />}
            rightSection={
              value && (
                <IconBackspace color='red' onClick={() => setValue('')} />
              )
            }
            styles={{ root: { width: '100%' } }}
          />
          <Tooltip label={t`Refresh search results`} position='bottom-end'>
            <ActionIcon
              size='lg'
              variant='transparent'
              onClick={() => searchQuery.refetch()}
            >
              <IconRefresh />
            </ActionIcon>
          </Tooltip>
          <Menu>
            <Menu.Target>
              <Tooltip label={t`Search Options`} position='bottom-end'>
                <ActionIcon size='lg' variant='transparent'>
                  <IconSettings />
                </ActionIcon>
              </Tooltip>
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
                />
              </Menu.Item>
              <Menu.Item>
                <Checkbox
                  label={t`Whole word search`}
                  checked={searchWhole}
                  onChange={(event) =>
                    setSearchWhole(event.currentTarget.checked)
                  }
                />
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      }
    >
      <Boundary label='SearchDrawer'>
        {searchQuery.isFetching && (
          <Center>
            <Loader />
          </Center>
        )}
        {!searchQuery.isFetching && !searchQuery.isError && (
          <Stack gap='md'>
            {queryResults.map((query, idx) => (
              <QueryResultGroup
                key={idx}
                query={query}
                onRemove={(query) => removeResults(query)}
                onResultClick={(query, pk, event) =>
                  onResultClick(query, pk, event)
                }
              />
            ))}
          </Stack>
        )}
        {searchQuery.isError && (
          <Alert
            color='red'
            radius='sm'
            variant='light'
            title={t`Error`}
            icon={<IconAlertCircle size='1rem' />}
          >
            <Trans>An error occurred during search query</Trans>
          </Alert>
        )}
        {searchText &&
          !searchQuery.isFetching &&
          !searchQuery.isError &&
          queryResults.length == 0 && (
            <Alert
              color='blue'
              radius='sm'
              variant='light'
              title={t`No Results`}
              icon={<IconSearch size='1rem' />}
            >
              <Trans>No results available for search query</Trans>
            </Alert>
          )}
      </Boundary>
    </Drawer>
  );
}
