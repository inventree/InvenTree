import { t } from '@lingui/macro';

import { ApiFormFieldType } from '../../components/forms/fields/ApiFormField';

/**
 * Construct a set of fields for creating / editing a Part instance
 */
export function partFields({
  editing = false,
  category_id
}: {
  editing?: boolean;
  category_id?: number;
}): ApiFormFieldType[] {
  let fields: ApiFormFieldType[] = [
    {
      name: 'category',
      value: category_id || undefined,
      filters: {
        strucural: false
      }
      // TODO: support secondary modal
    },
    {
      name: 'name'
    },
    {
      name: 'IPN'
    },
    {
      name: 'revision'
    },
    {
      name: 'description'
    },
    {
      name: 'variant_of'
    },
    {
      name: 'keywords'
      // TODO: icon 'fa-key'
    },
    {
      name: 'units'
    },
    {
      name: 'link'
      // TODO: icon 'fa-link'
    },
    {
      name: 'default_location',
      filters: {
        structural: false
      }
      // TODO: support secondary modal
      // TODO: icon 'fa-sitemap'
    },
    {
      name: 'default_expiry'
      // TODO: icon 'fa-calendar'
    },
    {
      name: 'minimum_stock'
      // TODO: icon 'fa-boxes',
    },
    {
      name: 'responsible'
      // TODO: icon 'fa-user'
    },
    {
      name: 'component'
      // TODO: group 'attributes'
      // TODO: default global_settings.PART_COMPONENT
    },
    {
      name: 'assembly'
      // TODO: group 'attributes'
      // TODO: default global_settings.PART_ASSEMBLY
    },
    {
      name: 'is_template'
      // TODO: group 'attributes'
      // TODO: default global_settings.PART_TEMPLATE
    },
    {
      name: 'trackable'
      // TODO: group 'attributes'
      // TODO: default global_settings.PART_TRACKABLE
    },
    {
      name: 'purchaseable'
      // TODO: group 'attributes'
      // TODO: default global_settings.PART_PURCHASEABLE
      // TODO: on edit, show / hide supplier group
    },
    {
      name: 'salable'
      // TODO: group 'attributes'
      // TODO: default global_settings.PART_SALABLE
    },
    {
      name: 'virtual'
      // TODO: group 'attributes'
      // TODO: default global_settings.PART_VIRTUAL
    },
    {
      name: 'active'
      // TODO: group 'attributes'
    }
  ];

  if (category_id != null) {
    // TODO: Set the value of the category field
  }

  if (!editing) {
    // TODO: Hide 'active' field
  }

  // TODO: pop 'expiry' field if expiry not enabled

  // TODO: pop 'revision' field if PART_ENABLE_REVISION is False

  // TODO: handle part duplications

  return fields;
}

/**
 * Construct a set of fields for creating / editing a PartCategory instance
 */
export function partCategoryFields({}: {}): ApiFormFieldType[] {
  return [
    {
      name: 'parent',
      description: t`Parent part category`,
      required: false
    },
    {
      name: 'name'
    },
    {
      name: 'description'
    },
    {
      name: 'default_location',
      filters: {
        structural: false
      }
      // TODO: icon 'fa-sitemap'
    },
    {
      name: 'default_keywords'
      // TODO: icon 'fa-key'
    },
    {
      name: 'structural'
    },
    {
      name: 'icon',
      // TODO: description
      // TODO: icon 'fa-image'
      placeholder: 'fas fa-tag'
    }
  ];
}
