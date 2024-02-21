import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import { useMemo } from 'react';

import { PanelGroup } from '../../../../components/nav/PanelGroup';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { InvenTreeIcon } from '../../../../functions/icons';
import { TemplateTable } from '../../../../tables/settings/TemplateTable';

export default function TemplateManagementPanel() {
  const templateTypes = useMemo(() => {
    return [
      {
        type: 'label',
        name: t`Labels`,
        singularName: t`Label`,
        apiEndpoints: ApiEndpoints.label_list,
        templateKey: 'label',
        variants: [
          {
            type: 'label',
            name: t`Part`,
            key: 'part',
            icon: 'part',
            itemKey: 'part'
          },
          {
            type: 'label',
            name: t`Location`,
            key: 'location',
            icon: 'default_location',
            itemKey: 'location'
          },
          {
            type: 'label',
            name: t`Stock item`,
            key: 'stock',
            icon: 'stock',
            itemKey: 'item'
          },
          {
            type: 'label',
            name: t`Build line`,
            key: 'buildline',
            icon: 'buildline',
            itemKey: 'line'
          }
        ]
      },
      {
        type: 'report',
        name: t`Reports`,
        singularName: t`Report`,
        apiEndpoints: ApiEndpoints.report_list,
        templateKey: 'template',
        variants: [
          {
            name: t`Purchase order`,
            key: 'po',
            icon: 'purchase_orders',
            itemKey: 'order'
          },
          {
            name: t`Sales order`,
            key: 'so',
            icon: 'sales_orders',
            itemKey: 'order'
          },
          {
            name: t`Return order`,
            key: 'ro',
            icon: 'return_orders',
            itemKey: 'order'
          },
          {
            name: t`Build`,
            key: 'build',
            icon: 'build_reports',
            itemKey: 'build'
          },
          {
            name: t`Bill of Materials`,
            key: 'bom',
            icon: 'bom',
            itemKey: 'part'
          },
          { name: t`Tests`, key: 'test', icon: 'test', itemKey: 'item' },
          {
            name: t`Stock location`,
            key: 'slr',
            icon: 'default_location',
            itemKey: 'location'
          }
        ]
      }
    ];
  }, []);

  const panels = useMemo(() => {
    return templateTypes.flatMap((templateType) => {
      return [
        // Add panel headline
        { name: templateType.type, label: templateType.name, disabled: true },

        // Add panel for each variant
        ...templateType.variants.map((variant) => {
          return {
            name: variant.key,
            label: variant.name,
            content: (
              <TemplateTable
                templateProps={{
                  apiEndpoint: templateType.apiEndpoints,
                  templateType: templateType.type as 'label' | 'report',
                  templateTypeTranslation: templateType.singularName,
                  variant: variant.key,
                  templateKey: templateType.templateKey,
                  preview: { itemKey: variant.itemKey }
                }}
              />
            ),
            icon: <InvenTreeIcon icon={variant.icon} />,
            showHeadline: false
          };
        })
      ];
    });
  }, [templateTypes]);

  return (
    <Stack>
      <PanelGroup
        pageKey="admin-center-templates"
        panels={panels}
        collapsible={false}
      />
    </Stack>
  );
}
