import type { ApiFormFieldType } from '@lib/types/Forms';
import { t } from '@lingui/core/macro';
import { IconList } from '@tabler/icons-react';

// Generic field for implementing a "duplication options" form field
export function DuplicateField({
  originalId,
  extraFields
}: Readonly<{
  originalId?: number | null;
  extraFields?: Record<string, any>;
}>): ApiFormFieldType {
  return {
    children: {
      original: {
        value: originalId,
        hidden: true
      },
      ...extraFields
    }
  };
}

// Generic field for rendering a list of tags within a form
export function TagsField({
  label,
  description,
  placeholder
}: Readonly<{
  label?: string;
  description?: string;
  placeholder?: string;
}>): ApiFormFieldType {
  return {
    field_type: 'tags',
    label: label ?? t`Tags`,
    description: description ?? t`Tags for this item`,
    placeholder: placeholder ?? t`Select tags`
  };
}

export function ProjectCodeField(): ApiFormFieldType {
  return {
    filters: {
      active: true
    },
    label: t`Project Code`,
    description: t`Select project code for this item`,
    icon: <IconList />
  };
}
