export const webUrl = '/web';

// Note: API requests are handled by the backend server
export const apiUrl = 'http://localhost:8000/api/';

export const homeUrl = `${webUrl}/home`;
export const loginUrl = `${webUrl}/login`;
export const logoutUrl = `${webUrl}/logout`;

export type UserType = {
  name?: string;
  username: string;
  testcred: string;
};

export const allaccessuser: UserType = {
  name: 'Ally Access',
  username: 'allaccess',
  testcred: 'nolimits'
};

export const adminuser: UserType = {
  username: 'admin',
  testcred: 'inventree'
};

export const stevenuser: UserType = {
  username: 'steven',
  testcred: 'wizardstaff'
};

export const readeruser: UserType = {
  username: 'reader',
  testcred: 'readonly'
};

export const noaccessuser: UserType = {
  username: 'noaccess',
  testcred: 'youshallnotpass'
};

export const engineeruser: UserType = {
  username: 'engineer',
  testcred: 'partsonly'
};

export const mockOidcPort = 9950;
export const mockOidcUrl = `http://localhost:${mockOidcPort}`;

/*
 * Identity always returned by the mock OIDC provider used in pui_sso.spec.ts
 * (see playwright/mock-oidc-server.mjs). It has no matching InvenTree
 * account, so logging in with it exercises the pending 'provider_signup'
 * flow. Consumed both by playwright.config.ts (to configure the mock
 * server's env and the backend's SSO provider settings) and by the test spec
 * itself, so both sides agree on the same values.
 */
export const mockSsoUser = {
  sub: 'mock-oidc-user-1',
  username: 'ssotestuser',
  email: 'ssotestuser@example.org',
  firstName: 'Sso',
  lastName: 'Testuser'
};
