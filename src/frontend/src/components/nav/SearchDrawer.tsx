import { Trans, t } from '@lingui/macro';
import {
  Accordion,
  ActionIcon,
  Alert,
  Anchor,
  Center,
  Checkbox,
  Drawer,
  Group,
  Loader,
  Menu,
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
  IconExclamationCircle,
  IconRefresh,
  IconSearch,
  IconSettings,
  IconTableExport,
  IconX
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { type NavigateFunction, useNavigate } from 'react-router-dom';

import { showNotification } from '@mantine/notifications';
import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { cancelEvent } from '../../functions/events';
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
  searchKey?: string;
  title?: string;
  overviewUrl?: string;
  enabled: boolean;
  parameters: any;
  results?: any;
};

/*
 * Render the results for a single search query
 */
function QueryResultGroup({
  searchText,
  query,
  navigate,
  onClose,
  onRemove,
  onResultClick
}: Readonly<{
  searchText: string;
  query: SearchQuery;
  navigate: NavigateFunction;
  onClose: () => void;
  onRemove: (query: ModelType) => void;
  onResultClick: (query: ModelType, pk: number, event: any) => void;
}>) {
  const modelInfo = useMemo(() => getModelInfo(query.model), [query.model]);

  const overviewUrl: string | undefined = useMemo(() => {
    // Query has a custom overview URL
    if (query.overviewUrl) {
      return query.overviewUrl;
    }

    return modelInfo.url_overview;
  }, [query, modelInfo]);

  // Callback function to view all results for a given query
  const viewResults = useCallback(
    (event: any) => {
      cancelEvent(event);

      if (overviewUrl) {
        const url = `${overviewUrl}?search=${searchText}`;

        // Close drawer if opening in the same tab
        if (!(event?.ctrlKey || event?.shiftKey)) {
          onClose();
        }

        navigateToLink(url, navigate, event);
      } else {
        showNotification({
          title: t`No Overview Available`,
          message: t`No overview available for this model type`,
          color: 'red',
          icon: <IconExclamationCircle />
        });
      }
    },
    [overviewUrl, searchText]
  );

  if (query.results.count == 0) {
    return null;
  }

  return (
    <Accordion.Item key={query.model} value={query.model}>
      <Accordion.Control component='div'>
        <Group justify='space-between'>
          <Group justify='left' gap={5} wrap='nowrap'>
            <Tooltip label={t`View all results`} position='top-start'>
              <ActionIcon
                size='sm'
                variant='transparent'
                radius='xs'
                aria-label={`view-all-results-${query.searchKey ?? query.model}`}
                disabled={!overviewUrl}
                onClick={viewResults}
              >
                <IconTableExport />
              </ActionIcon>
            </Tooltip>
            <Text size='lg'>{query.title ?? modelInfo.label_multiple}</Text>
            <Text size='sm' style={{ fontStyle: 'italic' }}>
              {' '}
              - {query.results.count} <Trans>results</Trans>
            </Text>
          </Group>
          <Group justify='right' wrap='nowrap'>
            <Tooltip label={t`Remove search group`} position='top-end'>
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
            </Tooltip>
            <Space />
          </Group>
        </Group>
      </Accordion.Control>
      <Accordion.Panel>
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
      </Accordion.Panel>
    </Accordion.Item>
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
        overviewUrl: '/purchasing/index/suppliers',
        searchKey: 'supplier',
        title: t`Suppliers`,
        parameters: {},
        enabled:
          user.hasViewRole(UserRoles.purchase_order) &&
          userSettings.isSet('SEARCH_PREVIEW_SHOW_COMPANIES')
      },
      {
        model: ModelType.company,
        overviewUrl: '/purchasing/index/manufacturers',
        searchKey: 'manufacturer',
        title: t`Manufacturers`,
        parameters: {},
        enabled:
          user.hasViewRole(UserRoles.purchase_order) &&
          userSettings.isSet('SEARCH_PREVIEW_SHOW_COMPANIES')
      },
      {
        model: ModelType.company,
        overviewUrl: '/sales/index/customers',
        searchKey: 'customer',
        title: t`Customers`,
        parameters: {},
        enabled:
          user.hasViewRole(UserRoles.sales_order) &&
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
        model: ModelType.salesordershipment,
        parameters: {},
        enabled:
          user.hasViewRole(UserRoles.sales_order) &&
          userSettings.isSet('SEARCH_PREVIEW_SHOW_SALES_ORDER_SHIPMENTS')
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
  const searchQueries: SearchQuery[] = useMemo(() => {
    return searchQueryList.filter((q) => q.enabled);
  }, [searchQueryList]);

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
      const key = query.searchKey || query.model;
      params[key] = query.parameters;
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
        (query) => (query.searchKey ?? query.model) in searchQuery.data
      );

      for (const key in searchQuery.data) {
        const query = queries.find((q) => (q.searchKey ?? q.model) == key);
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
          <Menu position='bottom-end'>
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
            <Accordion
              multiple
              defaultValue={searchQueries.map((q) => q.model)}
            >
              {queryResults.map((query, idx) => (
                <QueryResultGroup
                  key={idx}
                  searchText={searchText}
                  query={query}
                  navigate={navigate}
                  onClose={closeDrawer}
                  onRemove={(query) => removeResults(query)}
                  onResultClick={(query, pk, event) =>
                    onResultClick(query, pk, event)
                  }
                />
              ))}
            </Accordion>
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
