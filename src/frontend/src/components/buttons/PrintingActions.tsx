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

  const defaultLabelPlugin = useMemo(
    () => userSettings.getSetting('LABEL_DEFAULT_PRINTER'),
    [userSettings]
  );

  const [pluginKey, setPluginKey] = useState<string | null>(null);

  const labelPrintingEnabled = useMemo(() => {
    return enableLabels && globalSettings.isSet('LABEL_ENABLE');
  }, [enableLabels, globalSettings]);

  const reportPrintingEnabled = useMemo(() => {
    return enableReports && globalSettings.isSet('REPORT_ENABLE');
  }, [enableReports, globalSettings]);

  const [labelId, setLabelId] = useState<number | undefined>(undefined);
  const [reportId, setReportId] = useState<number | undefined>(undefined);

  useDataOutput({
    title: t`Printing Labels`,
    id: labelId
  });

  useDataOutput({
    title: t`Printing Reports`,
    id: reportId
  });

  const [itemIdList, setItemIdList] = useState<number[]>([]);

  const [labelDialogOpen, setLabelDialogOpen] = useState<boolean>(false);

  // Fetch available printing fields via OPTIONS request
  const printingFields = useQuery({
    enabled: labelDialogOpen && !!modelType && !!labelPrintingEnabled,
    queryKey: ['printingFields', modelType, pluginKey, labelDialogOpen],
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
        items: itemIdList.join(',')
      }
    };

    fields.items = {
      ...fields.items,
      value: itemIdList,
      hidden: true
    };

    fields['plugin'] = {
      ...fields['plugin'],
      default: defaultLabelPlugin,
      value: pluginKey,
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
  }, [defaultLabelPlugin, pluginKey, printingFields.data, itemIdList]);

  const labelModal = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.label_print),
    title: t`Print Label`,
    modalId: 'print-labels',
    fields: labelFields,
    timeout: 5000,
    onOpen: () => {
      setLabelDialogOpen(true);
      setItemIdList(items);
    },
    onClose: () => {
      setLabelDialogOpen(false);
      setPluginKey('');
    },
    submitText: t`Print`,
    successMessage: null,
    onFormSuccess: (response: any) => {
      setPluginKey('');
      setLabelId(response.pk);
    }
  });

  const reportFields: ApiFormFieldSet = useMemo(() => {
    return {
      template: {
        autoFill: true,
        filters: {
          enabled: true,
          model_type: modelType,
          items: itemIdList.join(',')
        }
      },
      items: {
        hidden: true,
        value: itemIdList
      }
    };
  }, [itemIdList, modelType]);

  const reportModal = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.report_print),
    title: t`Print Report`,
    modalId: 'print-reports',
    timeout: 5000,
    fields: reportFields,
    onOpen: () => {
      setItemIdList(items);
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
          position='bottom-start'
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
