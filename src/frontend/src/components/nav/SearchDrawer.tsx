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
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { ApiPaths } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { apiUrl } from '../../states/ApiState';
import { useUserSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';
import { RenderInstance } from '../render/Instance';
import { ModelInformationDict } from '../render/ModelType';

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
}: {
  query: SearchQuery;
  onRemove: (query: ModelType) => void;
  onResultClick: (query: ModelType, pk: number) => void;
}) {
  if (query.results.count == 0) {
    return null;
  }

  const model = ModelInformationDict[query.model];

  return (
    <Paper shadow="sm" radius="xs" p="md" key={`paper-${query.model}`}>
      <Stack key={`stack-${query.model}`}>
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
            onClick={() => onRemove(query.model)}
          >
            <IconX />
          </ActionIcon>
        </Group>
        <Divider />
        <Stack>
          {query.results.results.map((result: any) => (
            <Anchor
              onClick={() => onResultClick(query.model, result.pk)}
              key={result.pk}
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
}: {
  opened: boolean;
  onClose: () => void;
}) {
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
        parameters: {},
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
          location_detail: true
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
          supplier_detail: true
        },
        enabled:
          user.hasViewRole(UserRoles.purchase_order) &&
          userSettings.isSet(`SEARCH_PREVIEW_SHOW_PURCHASE_ORDERS`)
      },
      {
        model: ModelType.salesorder,
        parameters: {
          customer_detail: true
        },
        enabled:
          user.hasViewRole(UserRoles.sales_order) &&
          userSettings.isSet(`SEARCH_PREVIEW_SHOW_SALES_ORDERS`)
      },
      {
        model: ModelType.returnorder,
        parameters: {
          customer_detail: true
        },
        enabled:
          user.hasViewRole(UserRoles.return_order) &&
          userSettings.isSet(`SEARCH_PREVIEW_SHOW_RETURN_ORDERS`)
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

    let params: any = {
      offset: 0,
      limit: 10, // TODO: Make this configurable (based on settings)
      search: searchText,
      search_regex: searchRegex,
      search_whole: searchWhole
    };

    // Add in custom query parameters
    searchQueries.forEach((query) => {
      params[query.model] = query.parameters;
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
        (query) => query.model in searchQuery.data
      );

      for (let key in searchQuery.data) {
        let query = queries.find((q) => q.model == key);
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
  function onResultClick(query: ModelType, pk: number) {
    closeDrawer();
    const targetModel = ModelInformationDict[query];
    if (targetModel.url_detail == undefined) return;
    navigate(targetModel.url_detail.replace(':pk', pk.toString()));
  }

  return (
    <Drawer
      opened={opened}
      size="xl"
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
          {queryResults.map((query, idx) => (
            <QueryResultGroup
              key={idx}
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
