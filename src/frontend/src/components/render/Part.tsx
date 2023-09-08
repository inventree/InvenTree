import { ReactNode } from 'react';

import { RenderInlineModel } from './Instance';

/**
 * Inline rendering of a single Part instance
 */
export function RenderPart({ part }: { part: any }): ReactNode {
  return (
    <RenderInlineModel
      primary={part.name}
      secondary={part.description}
      image={part.thumnbnail || part.image}
    />
  );
}

/**
 * Inline rendering of a PartCategory instance
 */
export function RenderPartCategory({ category }: { category: any }): ReactNode {
  // TODO: Handle URL

  let lvl = '-'.repeat(category.level || 0);

  return (
    <RenderInlineModel
      primary={`${lvl} ${category.name}`}
      secondary={category.description}
    />
  );
}
