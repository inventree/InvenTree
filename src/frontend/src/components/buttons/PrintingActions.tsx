import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import { t } from '@lingui/core/macro';
import { Text } from '@mantine/core';
import {
  IconFileReport,
  IconPrinter,
  IconReport,
  IconTags
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { api } from '../../App';
import { extractAvailableFields } from '../../functions/forms';
import useDataOutput from '../../hooks/UseDataOutput';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsState';
import { ActionDropdown } from '../items/ActionDropdown';

export function PrintingActions({
  items,
  hidden,
  enableLabels,
  enableReports,
  modelType
}: {
  items: number[];
  hidden?: boolean;
  enableLabels?: boolean;
  enableReports?: boolean;
  modelType?: ModelType;
}) {
  const userSettings = useUserSettingsState();
  const globalSettings = useGlobalSettingsState();

  const hasSelectedItems = useMemo(() => items.length > 0, [items]);

  const [pluginKey, setPluginKey] = useState<string>('');

  const labelPrintingEnabled = useMemo(() => {
    return enableLabels && globalSettings.isSet('LABEL_ENABLE');
  }, [enableLabels, globalSettings]);

  const reportPrintingEnabled = useMemo(() => {
    return enableReports && globalSettings.isSet('REPORT_ENABLE');
  }, [enableReports, globalSettings]);

  const [labelId, setLabelId] = useState<number | undefined>(undefined);
  const [reportId, setReportId] = useState<number | undefined>(undefined);
  const [allPartsReportId, setAllPartsReportId] = useState<number | undefined>(
    undefined
  );
  const [allPartIds, setAllPartIds] = useState<number[]>([]);

  const labelProgress = useDataOutput({
    title: t`Printing Labels`,
    id: labelId
  });

  const reportProgress = useDataOutput({
    title: t`Printing Reports`,
    id: reportId
  });

  const allPartsReportProgress = useDataOutput({
    title: t`Printing All Parts Report`,
    id: allPartsReportId
  });

  // Fetch available printing fields via OPTIONS request
  const printingFields = useQuery({
    enabled: labelPrintingEnabled,
    queryKey: ['printingFields', modelType, pluginKey],
    gcTime: 500,
    queryFn: () =>
      api
        .options(apiUrl(ApiEndpoints.label_print), {
          params: {
            plugin: pluginKey || undefined
          }
        })
        .then((response: any) => {
          return extractAvailableFields(response, 'POST') || {};
        })
        .catch(() => {
          return {};
        })
  });

  const labelFields: ApiFormFieldSet = useMemo(() => {
    const fields: ApiFormFieldSet = printingFields.data || {};

    // Override field values
    fields.template = {
      ...fields.template,
      filters: {
        enabled: true,
        model_type: modelType,
        items: items.join(',')
      }
    };

    fields.items = {
      ...fields.items,
      value: items,
      hidden: true
    };

    fields['plugin'] = {
      ...fields['plugin'],
      value: userSettings.getSetting('LABEL_DEFAULT_PRINTER'),
      filters: {
        active: true,
        mixin: 'labels'
      },
      onValueChange: (value: string, record?: any) => {
        if (record?.key && record?.key != pluginKey) {
          setPluginKey(record.key);
        }
      }
    };

    return fields;
  }, [printingFields.data, items]);

  const labelModal = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.label_print),
    title: t`Print Label`,
    fields: labelFields,
    timeout: 5000,
    onClose: () => {
      setPluginKey('');
    },
    submitText: t`Print`,
    successMessage: null,
    onFormSuccess: (response: any) => {
      setPluginKey('');
      setLabelId(response.pk);
    }
  });

  const reportModal = useCreateApiFormModal({
    title: t`Print Report`,
    url: apiUrl(ApiEndpoints.report_print),
    timeout: 5000,
    fields: {
      template: {
        filters: {
          enabled: true,
          model_type: modelType,
          items: items.join(',')
        }
      },
      items: {
        hidden: true,
        value: items
      }
    },
    submitText: t`Print`,
    successMessage: null,
    onFormSuccess: (response: any) => {
      setReportId(response.pk);
    }
  });

  const allPartsReportModal = useCreateApiFormModal({
    title: t`Print All Parts Report`,
    url: apiUrl(ApiEndpoints.report_print),
    timeout: 120000, // Longer timeout for potentially large reports
    fields: {
      template: {
        filters: {
          enabled: true,
          model_type: 'allparts', // Use the new aggregate model type
          merge: true // Only show merge-enabled templates
        },
        label: t`Report Template`,
        description: t`Select a report template for all parts`
      },
      items: {
        hidden: true,
        value: allPartIds // Use state value
      }
    },
    preFormContent: (
      <div
        style={{
          marginBottom: '1rem',
          padding: '0.5rem',
          backgroundColor: '#f8f9fa',
          borderRadius: '4px'
        }}
      >
        <Text size='sm' c='dimmed'>
          <IconFileReport
            size={16}
            style={{ marginRight: '0.5rem', verticalAlign: 'middle' }}
          />
          {t`This will generate a report for ALL parts in the database (${allPartIds.length} parts), not just those visible on the current page.`}
        </Text>
      </div>
    ),
    submitText: t`Generate Report`,
    successMessage: null,
    onFormSuccess: async (response: any) => {
      setAllPartsReportId(response.pk);
    }
  });

  const fetchAllPartIds = async () => {
    try {
      const response = await api.get(apiUrl(ApiEndpoints.part_list), {
        params: {
          limit: 10000, // Adjust based on your needs
          active: true // Only active parts
        }
      });

      const partIds = response.data.results?.map((part: any) => part.pk) || [];
      setAllPartIds(partIds);

      // Open the modal after fetching IDs
      allPartsReportModal.open();
    } catch (error) {
      console.error('Failed to fetch all parts:', error);
    }
  };

  if (!modelType) {
    return null;
  }

  if (!labelPrintingEnabled && !reportPrintingEnabled) {
    return null;
  }

  return (
    !hidden && (
      <>
        {reportModal.modal}
        {labelModal.modal}
        {allPartsReportModal.modal}
        <ActionDropdown
          tooltip={t`Printing Actions`}
          icon={<IconPrinter />}
          disabled={false} // Always enable the dropdown
          actions={[
            {
              name: t`Print Labels`,
              icon: <IconTags />,
              onClick: () => labelModal.open(),
              hidden: !labelPrintingEnabled,
              disabled: !hasSelectedItems // Only enabled when items are selected
            },
            {
              name: t`Print Reports`,
              icon: <IconReport />,
              onClick: () => reportModal.open(),
              hidden: !reportPrintingEnabled,
              disabled: !hasSelectedItems // Only enabled when items are selected
            },
            {
              name: t`Print All Parts Report`,
              icon: <IconFileReport />,
              onClick: fetchAllPartIds,
              hidden: !reportPrintingEnabled || modelType !== 'part',
              disabled: false // Always enabled for parts
            }
          ]}
        />
      </>
    )
  );
}
