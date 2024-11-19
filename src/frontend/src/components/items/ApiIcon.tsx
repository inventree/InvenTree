import { useIconState } from '../../states/IconState';
import * as classes from './ApiIcon.css';

type ApiIconProps = {
  name: string;
  size?: number;
};

export const ApiIcon = ({ name: _name, size = 22 }: ApiIconProps) => {
  const [iconPackage, name, variant] = _name.split(':');
  const icon = useIconState(
    (s) => s.packagesMap[iconPackage]?.icons[name]?.variants[variant]
  );

  const unicode = icon ? String.fromCodePoint(Number.parseInt(icon, 16)) : '';

  if (!unicode) {
    console.warn(`ApiIcon not found: ${_name}`);
  }

  return (
    <i
      className={classes.icon}
      style={{
        fontFamily: `inventree-icon-font-${iconPackage}`,
        fontSize: size
      }}
    >
      {unicode}
    </i>
  );
};
