import { t } from '@lingui/macro';

import {
  ApiFormFieldSet,
  ApiFormFieldType
} from '../../components/forms/fields/ApiFormField';
import { ApiPaths } from '../../states/ApiState';
import { openCreateApiForm, openEditApiForm } from '../forms';

/**
 * Construct a set of fields for creating / editing a Part instance
 */
export function partFields({
  editing = false,
  category_id
}: {
  editing?: boolean;
  category_id?: number;
}): ApiFormFieldSet {
  let fields: ApiFormFieldSet = {
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
    responsible: {},
    component: {},
    assembly: {},
    is_template: {},
    trackable: {},
    purchaseable: {},
    salable: {},
    virtual: {},
    active: {}
  };

  if (category_id != null) {
    // TODO: Set the value of the category field
  }

  if (!editing) {
    // TODO: Hide 'active' field
  }

  // TODO: pop 'expiry' field if expiry not enabled
  delete fields['default_expiry'];

  // TODO: pop 'revision' field if PART_ENABLE_REVISION is False
  delete fields['revision'];

  // TODO: handle part duplications

  return fields;
}

/**
 * Launch a dialog to create a new Part instance
 */
export function createPart() {
  openCreateApiForm({
    name: 'part-create',
    title: t`Create Part`,
    url: ApiPaths.part_list,
    successMessage: t`Part created`,
    fields: partFields({})
  });
}

/**
 * Launch a dialog to edit an existing Part instance
 * @param part The ID of the part to edit
 */
export function editPart({
  part_id,
  callback
}: {
  part_id: number;
  callback?: () => void;
}) {
  openEditApiForm({
    name: 'part-edit',
    title: t`Edit Part`,
    url: ApiPaths.part_list,
    pk: part_id,
    successMessage: t`Part updated`,
    fields: partFields({ editing: true }),
    onFormSuccess: callback
  });
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
