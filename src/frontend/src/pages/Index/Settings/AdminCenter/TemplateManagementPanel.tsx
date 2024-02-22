import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import { useMemo } from 'react';

import { TemplatePreviewProps } from '../../../../components/editors/TemplateEditor/TemplateEditor';
import { ApiFormFieldSet } from '../../../../components/forms/fields/ApiFormField';
import { PanelGroup } from '../../../../components/nav/PanelGroup';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { ModelType } from '../../../../enums/ModelType';
import { InvenTreeIcon, InvenTreeIconType } from '../../../../functions/icons';
import { TemplateTable } from '../../../../tables/settings/TemplateTable';

type TemplateType = {
  type: 'label' | 'report';
  name: string;
  singularName: string;
  apiEndpoints: ApiEndpoints;
  templateKey: string;
  additionalFormFields?: ApiFormFieldSet;
  defaultTemplate: string;
  variants: {
    name: string;
    key: string;
    icon: InvenTreeIconType;
    preview: TemplatePreviewProps;
  }[];
};

const defaultLabelTemplate = `{% extends "label/label_base.html" %}

{% load l10n i18n barcode %}

{% block style %}

.qr {
    position: absolute;
    left: 0mm;
    top: 0mm;
    {% localize off %}
    height: {{ height }}mm;
    width: {{ height }}mm;
    {% endlocalize %}
}

{% endblock style %}

{% block content %}
<img class='qr' alt="{% trans 'QR Code' %}" src='{% qrcode qr_data %}'>

{% endblock content %}
`;

const defaultReportTemplate = `{% extends "report/inventree_report_base.html" %}

{% load i18n report barcode inventree_extras %}

{% block page_margin %}
margin: 2cm;
margin-top: 4cm;
{% endblock page_margin %}

{% block bottom_left %}
content: "v{{ report_revision }} - {{ date.isoformat }}";
{% endblock bottom_left %}

{% block bottom_center %}
content: "{% inventree_version shortstring=True %}";
{% endblock bottom_center %}

{% block style %}
<!-- Custom style -->
{% endblock style %}

{% block header_content %}
<!-- Custom header content -->
{% endblock header_content %}

{% block page_content %}
<!-- Custom page content -->
{% endblock page_content %}
`;

export default function TemplateManagementPanel() {
  const templateTypes = useMemo(() => {
    const templateTypes: TemplateType[] = [
      {
        type: 'label',
        name: t`Labels`,
        singularName: t`Label`,
        apiEndpoints: ApiEndpoints.label_list,
        templateKey: 'label',
        additionalFormFields: {
          width: {},
          height: {}
        },
        defaultTemplate: defaultLabelTemplate,
        variants: [
          {
            name: t`Part`,
            key: 'part',
            icon: 'part',
            preview: {
              itemKey: 'part',
              model: ModelType.part
            }
          },
          {
            name: t`Location`,
            key: 'location',
            icon: 'default_location',
            preview: {
              itemKey: 'location',
              model: ModelType.stocklocation
            }
          },
          {
            name: t`Stock item`,
            key: 'stock',
            icon: 'stock',
            preview: {
              itemKey: 'item',
              model: ModelType.stockitem
            }
          },
          {
            name: t`Build line`,
            key: 'buildline',
            icon: 'builds',
            preview: {
              itemKey: 'line',
              model: ModelType.build
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
        additionalFormFields: {
          page_size: {},
          landscape: {}
        },
        defaultTemplate: defaultReportTemplate,
        variants: [
          {
            name: t`Purchase order`,
            key: 'po',
            icon: 'purchase_orders',
            preview: {
              itemKey: 'order',
              model: ModelType.purchaseorder
            }
          },
          {
            name: t`Sales order`,
            key: 'so',
            icon: 'sales_orders',
            preview: {
              itemKey: 'order',
              model: ModelType.salesorder
            }
          },
          {
            name: t`Return order`,
            key: 'ro',
            icon: 'return_orders',
            preview: {
              itemKey: 'order',
              model: ModelType.returnorder
            }
          },
          {
            name: t`Build`,
            key: 'build',
            icon: 'builds',
            preview: {
              itemKey: 'build',
              model: ModelType.build
            }
          },
          {
            name: t`Bill of Materials`,
            key: 'bom',
            icon: 'bom',
            preview: {
              itemKey: 'part',
              model: ModelType.part,
              filters: { assembly: true }
            }
          },
          {
            name: t`Tests`,
            key: 'test',
            icon: 'test_templates',
            preview: {
              itemKey: 'item',
              model: ModelType.stockitem
            }
          },
          {
            name: t`Stock location`,
            key: 'slr',
            icon: 'default_location',
            preview: {
              itemKey: 'location',
              model: ModelType.stocklocation
            }
          }
        ]
      }
    ];

    return templateTypes;
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
                  preview: variant.preview,
                  additionalFormFields: templateType.additionalFormFields,
                  defaultTemplate: templateType.defaultTemplate
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
