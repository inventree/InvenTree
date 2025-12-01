import { ApiEndpoints, ModelType, apiUrl } from '@lib/index';
import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  ActionIcon,
  Badge,
  Box,
  Button,
  Center,
  Checkbox,
  Divider,
  Group,
  Loader,
  Paper,
  ScrollAreaAutosize,
  Select,
  Stack,
  Text,
  TextInput,
  Title,
  Tooltip
} from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { IconArrowDown, IconPlus, IconSearch } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import {
  type FormEventHandler,
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState
} from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../App';
import { usePartFields } from '../../forms/PartForms';
import { InvenTreeIcon } from '../../functions/icons';
import { useEditApiFormModal } from '../../hooks/UseForm';
import useWizard from '../../hooks/UseWizard';
import { StockItemTable } from '../../tables/stock/StockItemTable';
import { StandaloneField } from '../forms/StandaloneField';
import { RenderRemoteInstance } from '../render/Instance';

type SearchResult = {
  id: string;
  sku: string;
  name: string;
  exact: boolean;
  description?: string;
  price?: string;
  link?: string;
  image_url?: string;
  existing_part_id?: number;
};

type ImportResult = {
  manufacturer_part_id: number;
  supplier_part_id: number;
  part_id: number;
  pricing: { [priceBreak: number]: [number, string] };
  part_detail: any;
  parameters: {
    name: string;
    value: string;
    parameter_template: number | null;
    on_category: boolean;
  }[];
};

const SearchResult = ({
  searchResult,
  partId,
  rightSection
}: {
  searchResult: SearchResult;
  partId?: number;
  rightSection?: ReactNode;
}) => {
  return (
    <Paper key={searchResult.id} withBorder p='md' shadow='xs'>
      <Group justify='space-between' align='flex-start' gap='xs'>
        {searchResult.image_url && (
          <img
            src={searchResult.image_url}
            alt={searchResult.name}
            style={{ maxHeight: '50px' }}
          />
        )}
        <Stack gap={0} flex={1}>
          <a href={searchResult.link} target='_blank' rel='noopener noreferrer'>
            <Text size='lg' w={500}>
              {searchResult.name} ({searchResult.sku})
            </Text>
          </a>
          <Text size='sm'>{searchResult.description}</Text>
        </Stack>
        <Group gap='xs'>
          {searchResult.price && (
            <Text size='sm' c='primary'>
              {searchResult.price}
            </Text>
          )}
          {searchResult.exact && (
            <Badge size='sm' color='green'>
              <Trans>Exact Match</Trans>
            </Badge>
          )}
          {searchResult.existing_part_id &&
            partId &&
            searchResult.existing_part_id === partId && (
              <Badge size='sm' color='orange'>
                <Trans>Current part</Trans>
              </Badge>
            )}
          {searchResult.existing_part_id && (
            <Link to={`/part/${searchResult.existing_part_id}`}>
              <Badge size='sm' color='blue'>
                <Trans>Already Imported</Trans>
              </Badge>
            </Link>
          )}

          {rightSection}
        </Group>
      </Group>
    </Paper>
  );
};

const SearchStep = ({
  selectSupplierPart,
  partId
}: {
  selectSupplierPart: (props: {
    plugin: string;
    supplier: string;
    searchResult: SearchResult;
  }) => void;
  partId?: number;
}) => {
  const [searchValue, setSearchValue] = useState('');
  const [supplier, setSupplier] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const supplierQuery = useQuery<
    { plugin_slug: string; supplier_slug: string; supplier_name: string }[]
  >({
    queryKey: ['supplier-import-list'],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.plugin_supplier_list))
        .then((response) => response.data ?? []),
    enabled: true
  });

  const handleSearch = useCallback<FormEventHandler<HTMLFormElement>>(
    async (e) => {
      e.preventDefault();
      if (!searchValue || !supplier) return;

      setIsLoading(true);
      const [plugin_slug, supplier_slug] = JSON.parse(supplier);
      const res = await api.get(apiUrl(ApiEndpoints.plugin_supplier_search), {
        params: {
          plugin: plugin_slug,
          supplier: supplier_slug,
          term: searchValue
        }
      });
      setSearchResults(res.data ?? []);
      setIsLoading(false);
    },
    [supplier, searchValue]
  );

  useEffect(() => {
    if (
      supplier === '' &&
      supplierQuery.data &&
      supplierQuery.data.length > 0
    ) {
      setSupplier(
        JSON.stringify([
          supplierQuery.data[0].plugin_slug,
          supplierQuery.data[0].supplier_slug
        ])
      );
    }
  }, [supplierQuery.data]);

  return (
    <Stack>
      <form onSubmit={handleSearch}>
        <Group align='flex-end'>
          <TextInput
            aria-label='textbox-search-for-part'
            flex={1}
            placeholder='Search for a part'
            label={t`Search`}
            value={searchValue}
            onChange={(event) => setSearchValue(event.currentTarget.value)}
          />
          <Select
            label={t`Supplier`}
            value={supplier}
            onChange={(value) => setSupplier(value ?? '')}
            data={
              supplierQuery.data?.map((supplier) => ({
                value: JSON.stringify([
                  supplier.plugin_slug,
                  supplier.supplier_slug
                ]),
                label: supplier.supplier_name
              })) || []
            }
            searchable
            disabled={supplierQuery.isLoading || supplierQuery.isError}
            placeholder={
              supplierQuery.isLoading
                ? t`Loading...`
                : supplierQuery.isError
                  ? t`Error fetching suppliers`
                  : t`Select supplier`
            }
          />
          <Button
            color='blue'
            disabled={!searchValue || !supplier}
            type='submit'
            leftSection={<IconSearch />}
          >
            <Trans>Search</Trans>
          </Button>
        </Group>
      </form>

      {isLoading && (
        <Center>
          <Loader />
        </Center>
      )}

      {!isLoading && (
        <Text size='sm' c='dimmed'>
          <Trans>Found {searchResults.length} results</Trans>
        </Text>
      )}

      <ScrollAreaAutosize style={{ maxHeight: '49vh' }}>
        <Stack gap='xs'>
          {searchResults.map((res) => (
            <SearchResult
              key={res.id}
              searchResult={res}
              partId={partId}
              rightSection={
                !res.existing_part_id && (
                  <Tooltip label={t`Import this part`}>
                    <ActionIcon
                      aria-label={`action-button-import-part-${res.id}`}
                      onClick={() => {
                        const [plugin_slug, supplier_slug] =
                          JSON.parse(supplier);

                        selectSupplierPart({
                          plugin: plugin_slug,
                          supplier: supplier_slug,
                          searchResult: res
                        });
                      }}
                    >
                      <IconArrowDown size={18} />
                    </ActionIcon>
                  </Tooltip>
                )
              }
            />
          ))}
        </Stack>
      </ScrollAreaAutosize>
    </Stack>
  );
};

const CategoryStep = ({
  categoryId,
  importPart,
  isImporting
}: {
  isImporting: boolean;
  categoryId?: number;
  importPart: (categoryId: number) => void;
}) => {
  const [category, setCategory] = useState<number | undefined>(categoryId);

  return (
    <Stack>
      <StandaloneField
        fieldDefinition={{
          field_type: 'related field',
          api_url: apiUrl(ApiEndpoints.category_list),
          description: '',
          label: t`Select category`,
          model: ModelType.partcategory,
          filters: { structural: false },
          value: category,
          onValueChange: (value) => setCategory(value)
        }}
      />

      <Text>
        <Trans>
          Are you sure you want to import this part into the selected category
          now?
        </Trans>
      </Text>

      <Group justify='flex-end'>
        <Button
          aria-label='action-button-import-part-now'
          disabled={!category || isImporting}
          onClick={() => importPart(category!)}
          loading={isImporting}
        >
          <Trans>Import Now</Trans>
        </Button>
      </Group>
    </Stack>
  );
};

type ParametersType = (ImportResult['parameters'][number] & { use: boolean })[];

const ParametersStep = ({
  importResult,
  isImporting,
  skipStep,
  importParameters,
  parameterErrors
}: {
  importResult: ImportResult;
  isImporting: boolean;
  skipStep: () => void;
  importParameters: (parameters: ParametersType) => Promise<void>;
  parameterErrors: { template?: string; data?: string }[] | null;
}) => {
  const [parameters, setParameters] = useState<ParametersType>(() =>
    importResult.parameters.map((p) => ({
      ...p,
      use: p.parameter_template !== null
    }))
  );
  const [categoryCount, otherCount] = useMemo(() => {
    const c = parameters.filter((x) => x.on_category && x.use).length;
    const o = parameters.filter((x) => !x.on_category && x.use).length;
    return [c, o];
  }, [parameters]);
  const parametersFromCategory = useMemo(
    () => parameters.filter((x) => x.on_category).length,
    [parameters]
  );
  const setParameter = useCallback(
    (i: number, key: string) => (e: unknown) =>
      setParameters((p) => p.map((p, j) => (i === j ? { ...p, [key]: e } : p))),
    []
  );

  return (
    <Stack>
      <Text size='sm'>
        <Trans>
          Select and edit the parameters you want to add to this part.
        </Trans>
      </Text>

      {parametersFromCategory > 0 && (
        <Title order={5}>
          <Trans>Default category parameters</Trans>
          <Badge ml='xs'>{categoryCount}</Badge>
        </Title>
      )}
      <Stack gap='xs'>
        {parameters.map((p, i) => (
          <Stack key={i}>
            {p.on_category === false &&
              parameters[i - 1]?.on_category === true && (
                <>
                  <Divider />
                  <Title order={5}>
                    <Trans>Other parameters</Trans>
                    <Badge ml='xs'>{otherCount}</Badge>
                  </Title>
                </>
              )}
            <Group align='center' gap='xs'>
              <Checkbox
                checked={p.use}
                onChange={(e) =>
                  setParameter(i, 'use')(e.currentTarget.checked)
                }
              />
              {!p.on_category && (
                <Tooltip label={p.name}>
                  <Text
                    w='160px'
                    style={{
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}
                  >
                    {p.name}
                  </Text>
                </Tooltip>
              )}
              <Box flex={1}>
                <StandaloneField
                  hideLabels
                  fieldDefinition={{
                    field_type: 'related field',
                    model: ModelType.parametertemplate,
                    api_url: apiUrl(ApiEndpoints.parameter_template_list),
                    disabled: p.on_category,
                    value: p.parameter_template,
                    onValueChange: (v) => {
                      if (!p.parameter_template) setParameter(i, 'use')(true);
                      setParameter(i, 'parameter_template')(v);
                    },
                    error: parameterErrors?.[i]?.template
                  }}
                />
              </Box>
              <TextInput
                flex={1}
                value={p.value}
                onChange={(e) =>
                  setParameter(i, 'value')(e.currentTarget.value)
                }
                error={parameterErrors?.[i]?.data}
              />
            </Group>
          </Stack>
        ))}

        <Tooltip label={t`Add a new parameter`}>
          <ActionIcon
            onClick={() => {
              setParameters((p) => [
                ...p,
                {
                  name: '',
                  value: '',
                  parameter_template: null,
                  on_category: false,
                  use: true
                }
              ]);
            }}
          >
            <IconPlus size={18} />
          </ActionIcon>
        </Tooltip>
      </Stack>

      <Group justify='flex-end'>
        <Button onClick={skipStep}>
          <Trans>Skip</Trans>
        </Button>
        <Button
          aria-label='action-button-import-create-parameters'
          disabled={isImporting || parameters.filter((p) => p.use).length === 0}
          loading={isImporting}
          onClick={() => importParameters(parameters)}
        >
          <Trans>Create Parameters</Trans>
        </Button>
      </Group>
    </Stack>
  );
};

const StockStep = ({
  importResult,
  nextStep
}: {
  importResult: ImportResult;
  nextStep: () => void;
}) => {
  return (
    <Stack>
      <Text size='sm'>
        <Trans>Create initial stock for the imported part.</Trans>
      </Text>

      <StockItemTable
        tableName='initial-stock-creation'
        allowAdd
        showPricing
        showLocation
        params={{
          part: importResult.part_id,
          supplier_part: importResult.supplier_part_id,
          pricing: importResult.pricing,
          openNewStockItem: false
        }}
      />

      <Group justify='flex-end'>
        <Button onClick={nextStep} aria-label='action-button-import-stock-next'>
          <Trans>Next</Trans>
        </Button>
      </Group>
    </Stack>
  );
};

export default function ImportPartWizard({
  categoryId,
  partId
}: {
  categoryId?: number;
  partId?: number;
}) {
  const [supplierPart, setSupplierPart] = useState<{
    plugin: string;
    supplier: string;
    searchResult: SearchResult;
  }>();
  const [importResult, setImportResult] = useState<ImportResult>();
  const [isImporting, setIsImporting] = useState(false);
  const [parameterErrors, setParameterErrors] = useState<
    { template?: string; data?: string }[] | null
  >(null);

  const partFields = usePartFields({ create: false });
  const editPart = useEditApiFormModal({
    url: ApiEndpoints.part_list,
    pk: importResult?.part_id,
    title: t`Edit Part`,
    fields: partFields
  });

  const importPart = useCallback(
    async ({
      categoryId,
      partId
    }: { categoryId?: number; partId?: number }) => {
      setIsImporting(true);
      try {
        const importResult = await api.post(
          apiUrl(ApiEndpoints.plugin_supplier_import),
          {
            category_id: categoryId,
            part_import_id: supplierPart?.searchResult.id,
            plugin: supplierPart?.plugin,
            supplier: supplierPart?.supplier,
            part_id: partId
          },
          {
            timeout: 30000 // 30 seconds
          }
        );
        setImportResult(importResult.data);
        showNotification({
          title: t`Success`,
          message: t`Part imported successfully!`,
          color: 'green'
        });
        wizard.nextStep();
        setIsImporting(false);
      } catch (err: any) {
        showNotification({
          title: t`Error`,
          message:
            t`Failed to import part: ` +
            (err?.response?.data?.detail || err.message),
          color: 'red'
        });
        setIsImporting(false);
      }
    },
    [supplierPart]
  );

  // Render the select wizard step
  const renderStep = useCallback(
    (step: number) => {
      return (
        <Stack gap='xs'>
          {editPart.modal}

          {step > 0 && supplierPart && (
            <SearchResult
              searchResult={supplierPart?.searchResult}
              partId={partId}
              rightSection={
                importResult && (
                  <Group gap='xs'>
                    <Link to={`/part/${importResult.part_id}`} target='_blank'>
                      <InvenTreeIcon icon='part' />
                    </Link>
                    <ActionIcon
                      onClick={() => {
                        editPart.open();
                      }}
                    >
                      <InvenTreeIcon icon='edit' />
                    </ActionIcon>
                  </Group>
                )
              }
            />
          )}

          {step === 0 && (
            <SearchStep
              selectSupplierPart={(sp) => {
                setSupplierPart(sp);
                wizard.nextStep();
              }}
              partId={partId}
            />
          )}

          {!partId && step === 1 && (
            <CategoryStep
              isImporting={isImporting}
              categoryId={categoryId}
              importPart={(categoryId) => {
                importPart({ categoryId });
              }}
            />
          )}

          {!!partId && step === 1 && (
            <Stack>
              <RenderRemoteInstance model={ModelType.part} pk={partId} />

              <Text>
                <Trans>
                  Are you sure, you want to import the supplier and manufacturer
                  part into this part?
                </Trans>
              </Text>

              <Group justify='flex-end'>
                <Button
                  disabled={isImporting}
                  onClick={() => {
                    importPart({ partId });
                  }}
                  loading={isImporting}
                >
                  <Trans>Import</Trans>
                </Button>
              </Group>
            </Stack>
          )}

          {!partId && step === 2 && (
            <ParametersStep
              importResult={importResult!}
              isImporting={isImporting}
              parameterErrors={parameterErrors}
              importParameters={async (parameters) => {
                setIsImporting(true);
                setParameterErrors(null);
                const useParameters = parameters
                  .map((x, i) => ({ ...x, i }))
                  .filter((p) => p.use);
                const map = useParameters.reduce(
                  (acc, p, i) => {
                    acc[p.i] = i;
                    return acc;
                  },
                  {} as Record<number, number>
                );
                const createParameters = useParameters.map((p) => ({
                  model_type: 'part',
                  model_id: importResult!.part_id,
                  template: p.parameter_template,
                  data: p.value
                }));
                try {
                  await api.post(
                    apiUrl(ApiEndpoints.parameter_list),
                    createParameters
                  );
                  showNotification({
                    title: t`Success`,
                    message: t`Parameters created successfully!`,
                    color: 'green'
                  });
                  wizard.nextStep();
                  setIsImporting(false);
                } catch (err: any) {
                  if (
                    err?.response?.status === 400 &&
                    Array.isArray(err.response.data)
                  ) {
                    const errors = err.response.data.map(
                      (e: Record<string, string[]>) => {
                        const err: { data?: string; template?: string } = {};
                        if (e.data) err.data = e.data.join(',');
                        if (e.template) err.template = e.template.join(',');
                        return err;
                      }
                    );
                    setParameterErrors(
                      parameters.map((_, i) =>
                        map[i] !== undefined && errors[map[i]]
                          ? errors[map[i]]
                          : {}
                      )
                    );
                  }
                  showNotification({
                    title: t`Error`,
                    message: t`Failed to create parameters, please fix the errors and try again`,
                    color: 'red'
                  });
                  setIsImporting(false);
                }
              }}
              skipStep={() => wizard.nextStep()}
            />
          )}

          {step === (!partId ? 3 : 2) && (
            <StockStep
              importResult={importResult!}
              nextStep={() => wizard.nextStep()}
            />
          )}

          {step === (!partId ? 4 : 3) && (
            <Stack>
              <Text size='sm'>
                <Trans>
                  Part imported successfully from supplier{' '}
                  {supplierPart?.supplier}.
                </Trans>
              </Text>

              <Group justify='flex-end'>
                <Button
                  component={Link}
                  to={`/part/${importResult?.part_id}`}
                  variant='light'
                  aria-label='action-button-import-open-part'
                >
                  <Trans>Open Part</Trans>
                </Button>
                <Button
                  component={Link}
                  to={`/purchasing/supplier-part/${importResult?.supplier_part_id}`}
                  variant='light'
                >
                  <Trans>Open Supplier Part</Trans>
                </Button>
                <Button
                  component={Link}
                  to={`/purchasing/manufacturer-part/${importResult?.manufacturer_part_id}`}
                  variant='light'
                >
                  <Trans>Open Manufacturer Part</Trans>
                </Button>
                <Button
                  onClick={() => wizard.closeWizard()}
                  aria-label='action-button-import-close'
                >
                  <Trans>Close</Trans>
                </Button>
              </Group>
            </Stack>
          )}
        </Stack>
      );
    },
    [
      partId,
      categoryId,
      supplierPart,
      importResult,
      isImporting,
      parameterErrors,
      importPart,
      editPart.modal
    ]
  );

  const onClose = useCallback(() => {
    setSupplierPart(undefined);
    setImportResult(undefined);
    setIsImporting(false);
    setParameterErrors(null);
    wizard.setStep(0);
  }, []);

  // Create the wizard manager
  const wizard = useWizard({
    title: t`Import Supplier Part`,
    steps: [
      t`Search Supplier Part`,
      // if partId is provided, a inventree part already exists, just import the mp/sp
      ...(!partId ? [t`Category`, t`Parameters`] : [t`Confirm import`]),
      t`Stock`,
      t`Done`
    ],
    onClose,
    renderStep: renderStep,
    disableManualStepChange: true
  });

  return wizard;
}
