import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import { t } from '@lingui/core/macro';
import { IconPrinter, IconReport, IconTags } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { api } from '../../App';
import { extractAvailableFields } from '../../functions/forms';
import useDataOutput from '../../hooks/UseDataOutput';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsStates';
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

  const labelProgress = useDataOutput({
    title: t`Printing Labels`,
    id: labelId
  });

  const reportProgress = useDataOutput({
    title: t`Printing Reports`,
    id: reportId
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
  });

  const labelFields: ApiFormFieldSet = useMemo(() => {
    const fields: ApiFormFieldSet = printingFields.data || {};

    // Override field values
    fields.template = {
      ...fields.template,
      autoFill: true,
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
        autoFill: true,
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
