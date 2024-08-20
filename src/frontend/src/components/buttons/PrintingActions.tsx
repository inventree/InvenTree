import { t } from '@lingui/macro';
import { notifications } from '@mantine/notifications';
import { IconPrinter, IconReport, IconTags } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { extractAvailableFields } from '../../functions/forms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { apiUrl } from '../../states/ApiState';
import { useLocalState } from '../../states/LocalState';
import { ApiFormFieldSet } from '../forms/fields/ApiFormField';
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
  const { host } = useLocalState.getState();

  const enabled = useMemo(() => items.length > 0, [items]);

  const [pluginKey, setPluginKey] = useState<string>('');

  // Fetch available printing fields via OPTIONS request
  const printingFields = useQuery({
    enabled: enableLabels,
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
    let fields: ApiFormFieldSet = printingFields.data || {};

    // Override field values
    fields['template'] = {
      ...fields['template'],
      filters: {
        enabled: true,
        model_type: modelType,
        items: items.join(',')
      }
    };

    fields['items'] = {
      ...fields['items'],
      value: items,
      hidden: true
    };

    fields['plugin'] = {
      ...fields['plugin'],
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
    successMessage: t`Label printing completed successfully`,
    onFormSuccess: (response: any) => {
      setPluginKey('');
      if (!response.complete) {
        // TODO: Periodically check for completion (requires server-side changes)
        notifications.show({
          title: t`Error`,
          message: t`The label could not be generated`,
          color: 'red'
        });
        return;
      }

      if (response.output) {
        // An output file was generated
        const url = `${host}${response.output}`;
        window.open(url, '_blank');
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
    submitText: t`Generate`,
    successMessage: t`Report printing completed successfully`,
    onFormSuccess: (response: any) => {
      if (!response.complete) {
        // TODO: Periodically check for completion (requires server-side changes)
        notifications.show({
          title: t`Error`,
          message: t`The report could not be generated`,
          color: 'red'
        });
        return;
      }

      if (response.output) {
        // An output file was generated
        const url = `${host}${response.output}`;
        window.open(url, '_blank');
      }
    }
  });

  if (!modelType) {
    return null;
  }

  if (!enableLabels && !enableReports) {
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
              hidden: !enableLabels
            },
            {
              name: t`Print Reports`,
              icon: <IconReport />,
              onClick: () => reportModal.open(),
              hidden: !enableReports
            }
          ]}
        />
      </>
    )
  );
}
