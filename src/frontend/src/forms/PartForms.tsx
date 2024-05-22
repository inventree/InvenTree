import { t } from '@lingui/macro';
import { IconPackages } from '@tabler/icons-react';
import { useMemo, useState } from 'react';

import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';

/**
 * Construct a set of fields for creating / editing a Part instance
 */
export function usePartFields({
  create = false
}: {
  create?: boolean;
}): ApiFormFieldSet {
  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      category: {
        filters: {
          structural: false
        }
      },
      name: {},
      IPN: {},
      revision: {},
      description: {},
      variant_of: {},
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
      trackable: {},
      purchaseable: {},
      salable: {},
      virtual: {},
      active: {}
    };

    // Additional fields for creation
    if (create) {
      fields.copy_category_parameters = {};

      fields.initial_stock = {
        icon: <IconPackages />,
        children: {
          quantity: {},
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

    // TODO: pop 'expiry' field if expiry not enabled
    delete fields['default_expiry'];

    // TODO: pop 'revision' field if PART_ENABLE_REVISION is False
    delete fields['revision'];

    // TODO: handle part duplications

    return fields;
  }, [create]);
}

/**
 * Construct a set of fields for creating / editing a PartCategory instance
 */
export function partCategoryFields({}: {}): ApiFormFieldSet {
  let fields: ApiFormFieldSet = {
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
    icon: {}
  };

  return fields;
}

export function usePartParameterFields(): ApiFormFieldSet {
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
        onValueChange: (value: any, record: any) => {
          // Adjust the type of the "data" field based on the selected template
          if (record?.checkbox) {
            // This is a "checkbox" field
            setChoices([]);
            setFieldType('boolean');
          } else if (record?.choices) {
            let _choices: string[] = record.choices.split(',');

            if (_choices.length > 0) {
              setChoices(
                _choices.map((choice) => {
                  return {
                    label: choice.trim(),
                    value: choice.trim()
                  };
                })
              );
              setFieldType('choice');
            } else {
              setChoices([]);
              setFieldType('string');
            }
          } else {
            setChoices([]);
            setFieldType('string');
          }
        }
      },
      data: {
        field_type: fieldType,
        choices: fieldType === 'choice' ? choices : undefined,
        adjustValue: (value: any) => {
          // Coerce boolean value into a string (required by backend)
          return value.toString();
        }
      }
    };
  }, [fieldType, choices]);
}
