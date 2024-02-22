import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import { useMemo } from 'react';

import { PanelGroup } from '../../../../components/nav/PanelGroup';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { ModelType } from '../../../../enums/ModelType';
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
            preview: {
              itemKey: 'part',
              model: ModelType.part,
              apiUrl: ApiEndpoints.part_list
            }
          },
          {
            type: 'label',
            name: t`Location`,
            key: 'location',
            icon: 'default_location',
            preview: {
              itemKey: 'location',
              model: ModelType.stocklocation,
              apiUrl: ApiEndpoints.stock_location_list
            }
          },
          {
            type: 'label',
            name: t`Stock item`,
            key: 'stock',
            icon: 'stock',
            preview: {
              itemKey: 'item',
              model: ModelType.stockitem,
              apiUrl: ApiEndpoints.stock_item_list
            }
          },
          {
            type: 'label',
            name: t`Build line`,
            key: 'buildline',
            icon: 'buildline',
            preview: {
              itemKey: 'line',
              model: ModelType.build,
              apiUrl: ApiEndpoints.build_line_list
            }
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
            preview: {
              itemKey: 'order',
              model: ModelType.purchaseorder,
              apiUrl: ApiEndpoints.purchase_order_list
            }
          },
          {
            name: t`Sales order`,
            key: 'so',
            icon: 'sales_orders',
            preview: {
              itemKey: 'order',
              model: ModelType.salesorder,
              apiUrl: ApiEndpoints.sales_order_list
            }
          },
          {
            name: t`Return order`,
            key: 'ro',
            icon: 'return_orders',
            preview: {
              itemKey: 'order',
              model: ModelType.returnorder,
              apiUrl: ApiEndpoints.return_order_list
            }
          },
          {
            name: t`Build`,
            key: 'build',
            icon: 'build_reports',
            preview: {
              itemKey: 'build',
              model: ModelType.build,
              apiUrl: ApiEndpoints.build_line_list
            }
          },
          {
            name: t`Bill of Materials`,
            key: 'bom',
            icon: 'bom',
            preview: {
              itemKey: 'part',
              model: ModelType.part,
              apiUrl: ApiEndpoints.part_list,
              filters: { assembly: true }
            }
          },
          {
            name: t`Tests`,
            key: 'test',
            icon: 'test',
            preview: {
              itemKey: 'item',
              model: ModelType.stockitem,
              apiUrl: ApiEndpoints.stock_item_list
            }
          },
          {
            name: t`Stock location`,
            key: 'slr',
            icon: 'default_location',
            preview: {
              itemKey: 'location',
              model: ModelType.stocklocation,
              apiUrl: ApiEndpoints.stock_location_list
            }
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
                  preview: variant.preview
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
