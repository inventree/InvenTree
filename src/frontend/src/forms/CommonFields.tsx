import type { ApiFormFieldType } from '@lib/types/Forms';
import { t } from '@lingui/core/macro';

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
