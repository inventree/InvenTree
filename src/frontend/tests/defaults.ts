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
