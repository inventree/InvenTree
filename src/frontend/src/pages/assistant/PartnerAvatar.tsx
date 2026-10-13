import type { CSSProperties } from 'react';

const colors = [
  '#51b7a5',
  '#f5a337',
  '#7360ed',
  '#9460ed',
  '#3d82ef',
  '#e77932'
];
export default function PartnerAvatar({
  id,
  size = 44
}: { id: string; size?: number }) {
  const seed = [...id].reduce((sum, letter) => sum + letter.charCodeAt(0), 0);
  const variant = seed % 3;
  return (
    <svg
      className='partner-avatar'
      aria-hidden='true'
      viewBox='0 0 64 64'
      style={
        {
          width: size,
          height: size,
          '--partner-avatar-color': colors[seed % colors.length]
        } as CSSProperties
      }
    >
      {variant === 0 ? (
        <circle cx='32' cy='32' r='29' fill='var(--partner-avatar-color)' />
      ) : variant === 1 ? (
        <path
          d='M26 5C30 1 35 2 38 7L60 48C64 55 60 61 52 61H12C4 61 1 55 5 48Z'
          fill='var(--partner-avatar-color)'
        />
      ) : (
        <rect
          x='5'
          y='5'
          width='54'
          height='54'
          rx='20'
          transform='rotate(-24 32 32)'
          fill='var(--partner-avatar-color)'
        />
      )}
      <path
        d='m32 15 3 7m10-9 3 7'
        stroke='#172b2d'
        strokeWidth='4.5'
        strokeLinecap='round'
      />
    </svg>
  );
}
