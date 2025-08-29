import type { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';

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
        active: true, // Only show active parts when creating a new BOM item
        component: true
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
