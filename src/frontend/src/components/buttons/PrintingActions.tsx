import { t } from '@lingui/macro';
import { notifications, showNotification } from '@mantine/notifications';
import {
  IconCircleCheck,
  IconPrinter,
  IconReport,
  IconTags
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { api } from '../../App';
import { useApi } from '../../contexts/ApiContext';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import type { ModelType } from '../../enums/ModelType';
import { extractAvailableFields } from '../../functions/forms';
import { generateUrl } from '../../functions/urls';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { apiUrl } from '../../states/ApiState';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsState';
import type { ApiFormFieldSet } from '../forms/fields/ApiFormField';
import { ActionDropdown } from '../items/ActionDropdown';
import { ProgressBar } from '../items/ProgressBar';

/**
 * Hook to track the progress of a printing operation
 */
function usePrintingProgress({
  title,
  outputId,
  endpoint
}: {
  title: string;
  outputId?: number;
  endpoint: ApiEndpoints;
}) {
  const api = useApi();

  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!!outputId) {
      setLoading(true);
      showNotification({
        id: `printing-progress-${endpoint}-${outputId}`,
        title: title,
        loading: true,
        autoClose: false,
        withCloseButton: false,
        message: <ProgressBar size='lg' value={0} progressLabel />
      });
    } else {
      setLoading(false);
    }
  }, [outputId, endpoint, title]);

  const progress = useQuery({
    enabled: !!outputId && loading,
    refetchInterval: 750,
    queryKey: ['printingProgress', endpoint, outputId],
    queryFn: () =>
      api
        .get(apiUrl(endpoint, outputId))
        .then((response) => {
          const data = response?.data ?? {};

          if (data.pk && data.pk == outputId) {
            if (data.complete) {
              setLoading(false);
              notifications.hide(`printing-progress-${endpoint}-${outputId}`);

              notifications.show({
                title: t`Printing`,
                message: t`Printing completed successfully`,
                color: 'green',
                icon: <IconCircleCheck />
              });

              if (data.output) {
                const url = generateUrl(data.output);
                window.open(url.toString(), '_blank');
              }
            } else {
              notifications.update({
                id: `printing-progress-${endpoint}-${outputId}`,
                autoClose: false,
                withCloseButton: false,
                message: (
                  <ProgressBar
                    size='lg'
                    value={data.progress}
                    maximum={data.items}
                    progressLabel
                  />
                )
              });
            }
          }

          return data;
        })
        .catch(() => {
          notifications.hide(`printing-progress-${endpoint}-${outputId}`);
          setLoading(false);
          return {};
        })
  });
}

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

  const enabled = useMemo(() => items.length > 0, [items]);

  const [pluginKey, setPluginKey] = useState<string>('');

  const labelPrintingEnabled = useMemo(() => {
    return enableLabels && globalSettings.isSet('LABEL_ENABLE');
  }, [enableLabels, globalSettings]);

  const reportPrintingEnabled = useMemo(() => {
    return enableReports && globalSettings.isSet('REPORT_ENABLE');
  }, [enableReports, globalSettings]);

  const [labelId, setLabelId] = useState<number | undefined>(undefined);
  const [reportId, setReportId] = useState<number | undefined>(undefined);

  const labelProgress = usePrintingProgress({
    title: t`Printing Labels`,
    outputId: labelId,
    endpoint: ApiEndpoints.label_output
  });

  const reportProgress = usePrintingProgress({
    title: t`Printing Reports`,
    outputId: reportId,
    endpoint: ApiEndpoints.report_output
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
    timeout: (items.length + 1) * 5000,
    onClose: () => {
      setPluginKey('');
    },
    submitText: t`Print`,
    successMessage: null,
    onFormSuccess: (response: any) => {
      setPluginKey('');
      if (!response.complete) {
        setLabelId(response.pk);
      }
    }
  });

  const reportModal = useCreateApiFormModal({
    title: t`Print Report`,
    url: apiUrl(ApiEndpoints.report_print),
    timeout: (items.length + 1) * 5000,
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
        <ActionDropdown
          tooltip={t`Printing Actions`}
          icon={<IconPrinter />}
          disabled={!enabled}
          actions={[
            {
              name: t`Print Labels`,
              icon: <IconTags />,
              onClick: () => labelModal.open(),
              hidden: !labelPrintingEnabled
            },
            {
              name: t`Print Reports`,
              icon: <IconReport />,
              onClick: () => reportModal.open(),
              hidden: !reportPrintingEnabled
            }
          ]}
        />
      </>
    )
  );
}
