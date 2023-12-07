import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';

/**
 * Field set for BomItem form
 */
export function bomItemFields(): ApiFormFieldSet {
  return {
    part: {
      hidden: true
    },
    sub_part: {
      filters: {
        component: true,
        virtual: false
      }
    },
    quantity: {},
    reference: {},
    overage: {},
    note: {},
    allow_variants: {},
    inherited: {},
    consumable: {},
    optional: {}
  };
}
