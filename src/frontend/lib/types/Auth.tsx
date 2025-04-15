export interface AuthContext {
  status: number;
  data: { flows: Flow[] };
  meta: { is_authenticated: boolean };
}

export enum FlowEnum {
  VerifyEmail = 'verify_email',
  Login = 'login',
  Signup = 'signup',
  ProviderRedirect = 'provider_redirect',
  ProviderSignup = 'provider_signup',
  ProviderToken = 'provider_token',
  MfaAuthenticate = 'mfa_authenticate',
  Reauthenticate = 'reauthenticate',
  MfaReauthenticate = 'mfa_reauthenticate'
}

export interface Flow {
  id: FlowEnum;
  providers?: string[];
  is_pending?: boolean[];
}

export interface AuthProvider {
  id: string;
  name: string;
  flows: string[];
  client_id: string;
}

export interface AuthConfig {
  account: {
    authentication_method: string;
  };
  socialaccount: { providers: AuthProvider[] };
  mfa: {
    supported_types: string[];
  };
  usersessions: {
    track_activity: boolean;
  };
}

// Errors
export type ErrorResponse = {
  data: any;
  status: number;
  statusText: string;
  message?: string;
};
