import { IconUsers } from '@tabler/icons-react';

import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';

export function projectCodeFields(): ApiFormFieldSet {
  return {
    code: {},
    description: {},
    responsible: {
      icon: <IconUsers />
    }
  };
}

export function customStateFields(): ApiFormFieldSet {
  return {
    key: {},
    name: {},
    label: {},
    color: {},
    logical_key: {},
    model: {},
    reference_status: {}
  };
}

export function customUnitsFields(): ApiFormFieldSet {
  return {
    name: {},
    definition: {},
    symbol: {}
  };
}

export function extraLineItemFields(): ApiFormFieldSet {
  return {
    order: {
      hidden: true
    },
    reference: {},
    description: {},
    quantity: {},
    price: {},
    price_currency: {},
    notes: {},
    link: {}
  };
}

export function selectionListFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
    locked: {},
    source_plugin: {},
    source_string: {},
    default: {}
    //choices: {},
  };
}
