import { t } from '@lingui/macro';
import { IconPackages } from '@tabler/icons-react';
import { useMemo, useState } from 'react';

import type { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';
import { useApi } from '../contexts/ApiContext';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from '../states/ApiState';
import { useGlobalSettingsState } from '../states/SettingsState';

/**
 * Construct a set of fields for creating / editing a Part instance
 */
export function usePartFields({
  create = false
}: {
  create?: boolean;
}): ApiFormFieldSet {
  const settings = useGlobalSettingsState();

  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      category: {
        filters: {
          structural: false
        }
      },
      name: {},
      IPN: {},
      description: {},
      revision: {},
      revision_of: {
        filters: {
          is_revision: false,
          is_template: false
        }
      },
      variant_of: {
        filters: {
          is_template: true
        }
      },
      keywords: {},
      units: {},
      link: {},
      default_location: {
        filters: {
          structural: false
        }
      },
      default_expiry: {},
      minimum_stock: {},
      responsible: {
        filters: {
          is_active: true
        }
      },
      component: {},
      assembly: {},
      is_template: {},
      testable: {},
      trackable: {},
      purchaseable: {},
      salable: {},
      virtual: {},
      locked: {},
      active: {},
      starred: {
        field_type: 'boolean',
        label: t`Subscribed`,
        description: t`Subscribe to notifications for this part`,
        disabled: false,
        required: false
      }
    };

    // Additional fields for creation
    if (create) {
      fields.copy_category_parameters = {};

      fields.initial_stock = {
        icon: <IconPackages />,
        children: {
          quantity: {
            value: 0
          },
          location: {}
        }
      };

      fields.initial_supplier = {
        children: {
          supplier: {
            filters: {
              is_supplier: true
            }
          },
          sku: {},
          manufacturer: {
            filters: {
              is_manufacturer: true
            }
          },
          mpn: {}
        }
      };
    }

    if (settings.isSet('PART_REVISION_ASSEMBLY_ONLY')) {
      fields.revision_of.filters['assembly'] = true;
    }

    // Pop 'revision' field if PART_ENABLE_REVISION is False
    if (!settings.isSet('PART_ENABLE_REVISION')) {
      delete fields['revision'];
      delete fields['revision_of'];
    }

    // Pop 'expiry' field if expiry not enabled
    if (!settings.isSet('STOCK_ENABLE_EXPIRY')) {
      delete fields['default_expiry'];
    }

    if (create) {
      delete fields['starred'];
    }

    return fields;
  }, [create, settings]);
}

/**
 * Construct a set of fields for creating / editing a PartCategory instance
 */
export function partCategoryFields({
  create
}: {
  create?: boolean;
}): ApiFormFieldSet {
  const fields: ApiFormFieldSet = useMemo(() => {
    const fields: ApiFormFieldSet = {
      parent: {
        description: t`Parent part category`,
        required: false
      },
      name: {},
      description: {},
      default_location: {
        filters: {
          structural: false
        }
      },
      default_keywords: {},
      structural: {},
      starred: {
        field_type: 'boolean',
        label: t`Subscribed`,
        description: t`Subscribe to notifications for this category`,
        disabled: false,
        required: false
      },
      icon: {
        field_type: 'icon'
      }
    };

    if (create) {
      delete fields['starred'];
    }

    return fields;
  }, [create]);

  return fields;
}

export function usePartParameterFields({
  editTemplate
}: {
  editTemplate?: boolean;
}): ApiFormFieldSet {
  const api = useApi();

  // Valid field choices
  const [choices, setChoices] = useState<any[]>([]);

  // Field type for "data" input
  const [fieldType, setFieldType] = useState<'string' | 'boolean' | 'choice'>(
    'string'
  );

  return useMemo(() => {
    return {
      part: {
        disabled: true
      },
      template: {
        disabled: editTemplate == false,
        onValueChange: (value: any, record: any) => {
          // Adjust the type of the "data" field based on the selected template
          if (record?.checkbox) {
            // This is a "checkbox" field
            setChoices([]);
            setFieldType('boolean');
          } else if (record?.choices) {
            const _choices: string[] = record.choices.split(',');

            if (_choices.length > 0) {
              setChoices(
                _choices.map((choice) => {
                  return {
                    display_name: choice.trim(),
                    value: choice.trim()
                  };
                })
              );
              setFieldType('choice');
            } else {
              setChoices([]);
              setFieldType('string');
            }
          } else if (record?.selectionlist) {
            api
              .get(
                apiUrl(ApiEndpoints.selectionlist_detail, record.selectionlist)
              )
              .then((res) => {
                setChoices(
                  res.data.choices.map((item: any) => {
                    return {
                      value: item.value,
                      display_name: item.label
                    };
                  })
                );
                setFieldType('choice');
              });
          } else {
            setChoices([]);
            setFieldType('string');
          }
        }
      },
      data: {
        type: fieldType,
        field_type: fieldType,
        choices: fieldType === 'choice' ? choices : undefined,
        adjustValue: (value: any) => {
          // Coerce boolean value into a string (required by backend)
          return value.toString();
        }
      }
    };
  }, [editTemplate, fieldType, choices]);
}

export function partStocktakeFields(): ApiFormFieldSet {
  return {
    part: {
      hidden: true
    },
    quantity: {},
    item_count: {},
    cost_min: {},
    cost_min_currency: {},
    cost_max: {},
    cost_max_currency: {},
    note: {}
  };
}

export function generateStocktakeReportFields(): ApiFormFieldSet {
  return {
    part: {},
    category: {},
    location: {},
    exclude_external: {},
    generate_report: {},
    update_parts: {}
  };
}
