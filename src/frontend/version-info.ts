/**
 * Extract package version information from package.json
 */

import { readFileSync } from 'node:fs';

const packageJson = JSON.parse(readFileSync('./package.json', 'utf-8'));

// Function to get the version of a specific package
function getPackageVersion(pkg: string) {
  const version: string =
    packageJson.dependencies[pkg] ||
    packageJson.peerDependencies[pkg] ||
    packageJson.devDependencies[pkg];

  if (!version) {
    throw new Error(`Package ${pkg} not found in package.json`);
  }

  // Strip any version prefix (e.g. "^", "~", "@")
  const versionMatch = version.match(/(\d+\.\d+\.\d+)/);
  if (!versionMatch) {
    throw new Error(`Invalid version format for package ${pkg}: ${version}`);
  }

  return JSON.stringify(versionMatch[0]);
}

// Export InvenTree package information
export const INVENTREE_LIB_VERSION: string = JSON.stringify(
  packageJson.version
);

// Export information about other core package versions
// This is because we need to ensure that the versions of these packages are compatible with plugins
export const __INVENTREE_VERSION_INFO__ = {
  __INVENTREE_LIB_VERSION__: INVENTREE_LIB_VERSION,
  __INVENTREE_REACT_VERSION__: getPackageVersion('react'),
  __INVENTREE_REACT_DOM_VERSION__: getPackageVersion('react-dom'),
  __INVENTREE_MANTINE_VERSION__: getPackageVersion('@mantine/core')
};
