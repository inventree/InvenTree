import { t } from '@lingui/core/macro';
import { IconBuildingStore, IconCopy, IconPackages } from '@tabler/icons-react';
import { useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import { useApi } from '../contexts/ApiContext';
import { useGlobalSettingsState } from '../states/SettingsStates';

/**
 * Construct a set of fields for creating / editing a Part instance
 */
export function usePartFields({
  create = false,
  duplicatePartInstance
}: {
  duplicatePartInstance?: any;
  create?: boolean;
}): ApiFormFieldSet {
  const settings = useGlobalSettingsState();

  const [virtual, setVirtual] = useState<boolean>(false);
  const [purchaseable, setPurchaseable] = useState<boolean>(false);

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
      purchaseable: {
        value: purchaseable,
        onValueChange: (value: boolean) => {
          setPurchaseable(value);
        }
      },
      salable: {},
      virtual: {
        value: virtual,
        onValueChange: (value: boolean) => {
          setVirtual(value);
        }
      },
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

      if (!virtual) {
        fields.initial_stock = {
          icon: <IconPackages />,
          children: {
            quantity: {
              value: 0
            },
            location: {}
          }
        };
      }

      if (purchaseable) {
        fields.initial_supplier = {
          icon: <IconBuildingStore />,
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
    }

    // Additional fields for part duplication
    if (create && duplicatePartInstance?.pk) {
      fields.duplicate = {
        icon: <IconCopy />,
        children: {
          part: {
            value: duplicatePartInstance?.pk,
            hidden: true
          },
          copy_image: {
            value: true
          },
          copy_bom: {
            value: settings.isSet('PART_COPY_BOM'),
            hidden: !duplicatePartInstance?.assembly
          },
          copy_notes: {
            value: true
          },
          copy_parameters: {
            value: settings.isSet('PART_COPY_PARAMETERS')
          },
          copy_tests: {
            value: true,
            hidden: !duplicatePartInstance?.testable
          }
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
  }, [virtual, purchaseable, create, duplicatePartInstance, settings]);
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
        default: fieldType === 'boolean' ? false : undefined,
        adjustValue: (value: any) => {
          // Coerce boolean value into a string (required by backend)

          let v: string = value.toString().trim();

          if (fieldType === 'boolean') {
            if (v.toLowerCase() !== 'true') {
              v = 'false';
            }
          }

          return v;
        }
      },
      note: {}
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
