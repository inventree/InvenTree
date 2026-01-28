import {
  type CredentialRequestOptionsJSON,
  get,
  parseRequestOptionsFromJSON
} from '@github/webauthn-json/browser-ponyfill';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { type AuthProvider, FlowEnum } from '@lib/types/Auth';
import { t } from '@lingui/core/macro';
import { notifications, showNotification } from '@mantine/notifications';
import axios from 'axios';
import type { AxiosRequestConfig } from 'axios';
import type { Location, NavigateFunction } from 'react-router-dom';
import { api, setApiDefaults } from '../App';
import { useLocalState } from '../states/LocalState';
import { useServerApiState } from '../states/ServerApiState';
import { useUserState } from '../states/UserState';
import { fetchGlobalStates } from '../states/states';
import { showLoginNotification } from './notifications';
import { generateUrl } from './urls';

export function followRedirect(navigate: NavigateFunction, redirect: any) {
  let url = redirect?.redirectUrl ?? '/home';

  if (redirect?.queryParams) {
    // Construct and appand query parameters
    url = `${url}?${new URLSearchParams(redirect.queryParams).toString()}`;
  }

  navigate(url);
}

/**
 * sends a request to the specified url from a form. this will change the window location.
 * @param {string} path the path to send the post request to
 * @param {object} params the parameters to add to the url
 * @param {string} [method=post] the method to use on the form
 *
 * Source https://stackoverflow.com/questions/133925/javascript-post-request-like-a-form-submit/133997#133997
 */

function post(path: string, params: any, method = 'post') {
  const form = document.createElement('form');
  form.method = method;
  form.action = path;

  for (const key in params) {
    if (
      params.hasOwn?.(key) ||
      Object.prototype.hasOwnProperty.call(params, key)
    ) {
      const hiddenField = document.createElement('input');
      hiddenField.type = 'hidden';
      hiddenField.name = key;
      hiddenField.value = params[key];

      form.appendChild(hiddenField);
    }
  }

  document.body.appendChild(form);
  form.submit();
}

/**
 * Attempt to login using username:password combination.
 * If login is successful, an API token will be returned.
 * This API token is used for any future API requests.
 */
export async function doBasicLogin(
  username: string,
  password: string,
  navigate: NavigateFunction,
  code?: string
) {
  const { getHost } = useLocalState.getState();
  const { clearUserState, setAuthenticated, fetchUserState } =
    useUserState.getState();
  const { setAuthContext, setMfaContext } = useServerApiState.getState();

  if (username.length == 0 || password.length == 0) {
    return;
  }

  clearCsrfCookie();
  await ensureCsrf();

  let loginDone = false;
  let success = false;

  const host: string = getHost();

  // Attempt login with basic info
  await api
    .post(
      apiUrl(ApiEndpoints.auth_login),
      {
        username: username,
        password: password
      },
      {
        baseURL: host
      }
    )
    .then((response) => {
      setAuthContext(response.data?.data);
      if (response.status == 200 && response.data?.meta?.is_authenticated) {
        setAuthenticated(true);
        loginDone = true;
        success = true;
      }
    })
    .catch(async (err) => {
      notifications.hide('auth-login-error');

      if (err?.response?.status) {
        switch (err.response.status) {
          case 401:
            await handlePossibleMFAError(err);
            break;
          case 409:
            doLogout(navigate);
            notifications.show({
              title: t`Logged Out`,
              message: t`There was a conflicting session for this browser, which has been logged out.`,
              color: 'red',
              id: 'auth-login-error',
              autoClose: true
            });
            break;
          default:
            notifications.show({
              title: `${t`Login failed`} (${err.response.status})`,
              message: t`Check your input and try again.`,
              id: 'auth-login-error',
              color: 'red'
            });
            break;
        }
      } else {
        notifications.show({
          title: t`Login failed`,
          message: t`No response from server.`,
          color: 'red',
          id: 'login-error'
        });
      }
    });

  // see if mfa registration is required
  if (loginDone) {
    // stop further processing if mfa setup is required
    if (!(await MfaSetupOk(navigate))) loginDone = false;
  }

  // we are successfully logged in - gather required states for app
  if (loginDone) {
    await fetchUserState();
    await fetchGlobalStates();
    observeProfile();
  } else if (!success) {
    clearUserState();
  }
  return success;

  async function handlePossibleMFAError(err: any) {
    setAuthContext(err.response.data?.data);
    const mfa_flow = err.response.data.data.flows.find(
      (flow: any) => flow.id == FlowEnum.MfaAuthenticate
    );
    if (mfa_flow?.is_pending) {
      setMfaContext(mfa_flow);
      // MFA is required - we might already have a code
      if (code && code.length > 0) {
        const rslt = await handleMfaLogin(
          navigate,
          undefined,
          { code: code },
          () => {}
        );
        if (rslt) {
          setAuthenticated(true);
          loginDone = true;
          success = true;
          notifications.show({
            title: t`MFA Login successful`,
            message: t`MFA details were automatically provided in the browser`,
            color: 'green'
          });
        }
      }
      // No code or success - off to the mfa page
      if (!loginDone) {
        success = true;
        navigate('/mfa');
      }
    }
  }
}

/**
 * Logout the user from the current session
 *
 * @arg deleteToken: If true, delete the token from the server
 */
export const doLogout = async (navigate: NavigateFunction) => {
  const { clearUserState, isLoggedIn } = useUserState.getState();
  const { setAuthContext } = useServerApiState.getState();

  // Logout from the server session
  if (isLoggedIn() || !!getCsrfCookie()) {
    await authApi(apiUrl(ApiEndpoints.auth_session), undefined, 'delete').catch(
      () => {}
    );
    showLoginNotification({
      title: t`Logged Out`,
      message: t`Successfully logged out`
    });
  }

  clearUserState();
  clearCsrfCookie();
  setAuthContext(undefined);
  navigate('/login');
};

export const doSimpleLogin = async (email: string) => {
  const { getHost } = useLocalState.getState();
  const mail = await axios
    .post(
      apiUrl(ApiEndpoints.user_simple_login),
      {
        email: email
      },
      {
        baseURL: getHost(),
        timeout: 2000
      }
    )
    .then((response) => response.data)
    .catch((_error) => {
      return false;
    });
  return mail;
};

function MfaSetupOk(navigate: NavigateFunction) {
  return api
    .get(apiUrl(ApiEndpoints.auth_base))
    .then(() => {
      return true;
    })
    .catch((err) => {
      if (err?.response?.status == 401) {
        const mfa_register = err.response.data.id == FlowEnum.MfaRegister;
        if (mfa_register && navigate != undefined) {
          navigate('/mfa-setup');
          return false;
        }
      } else {
        console.error(err);
      }
      return true;
    });
}

function observeProfile() {
  // overwrite language and theme info in session with profile info

  const user = useUserState.getState().getUser();
  const { language, setLanguage, userTheme, setTheme, setWidgets, setLayouts } =
    useLocalState.getState();
  if (user) {
    if (user.profile?.language && language != user.profile.language) {
      showNotification({
        title: t`Language changed`,
        message: t`Your active language has been changed to the one set in your profile`,
        color: 'blue',
        icon: 'language'
      });
      setLanguage(user.profile.language, true);
    }

    if (user.profile?.theme) {
      // extract keys of usertheme and set them to the values of user.profile.theme
      const newTheme = Object.keys(userTheme).map((key) => {
        return {
          key: key as keyof typeof userTheme,
          value: user.profile.theme[key] as string
        };
      });
      const diff = newTheme.filter(
        (item) => userTheme[item.key] !== item.value
      );
      if (diff.length > 0) {
        showNotification({
          title: t`Theme changed`,
          message: t`Your active theme has been changed to the one set in your profile`,
          color: 'blue'
        });
        setTheme(newTheme);
      }
    }

    if (user.profile?.widgets) {
      const data = user.profile.widgets;
      // split data into widgets and layouts (either might be undefined)
      const widgets = data.widgets ?? [];
      const layouts = data.layouts ?? {};
      setWidgets(widgets, true);
      setLayouts(layouts, true);
    }
  }
}

export async function ensureCsrf() {
  const cookie = getCsrfCookie();
  if (cookie == undefined) {
    await api.get(apiUrl(ApiEndpoints.auth_session)).catch(() => {});
  }
}

export function handleReset(
  navigate: NavigateFunction,
  values: { email: string }
) {
  ensureCsrf();
  api.post(apiUrl(ApiEndpoints.user_reset), values).then((val) => {
    if (val.status === 200) {
      notifications.show({
        title: t`Mail delivery successful`,
        message: t`Check your inbox for a reset link. This only works if you have an account. Check in spam too.`,
        color: 'green',
        autoClose: false
      });
      navigate('/login');
    } else {
      notifications.show({
        title: t`Reset failed`,
        message: t`Check your input and try again.`,
        color: 'red'
      });
    }
  });
}

export async function handleMfaLogin(
  navigate: NavigateFunction,
  location: Location<any> | undefined,
  values: { code: string; remember?: boolean },
  setError: (message: string | undefined) => void
) {
  const { setAuthContext } = useServerApiState.getState();

  return await authApi(apiUrl(ApiEndpoints.auth_login_2fa), undefined, 'post', {
    code: values.code
  })
    .then((response) => {
      handleSuccessFullAuth(response, navigate, location, setError);
      return true;
    })
    .catch(async (err) => {
      // Already logged in, but with a different session
      if (err?.response?.status == 409) {
        notifications.show({
          title: t`Already logged in`,
          message: t`There is a conflicting session on the server for this browser. Please logout of that first.`,
          color: 'red',
          autoClose: false
        });
        // MFA trust flow pending
      } else if (err?.response?.status == 401) {
        const mfa_trust = err.response.data.data.flows.find(
          (flow: any) => flow.id == FlowEnum.MfaTrust
        );
        if (mfa_trust?.is_pending) {
          setAuthContext(err.response.data.data);
          await authApi(apiUrl(ApiEndpoints.auth_trust), undefined, 'post', {
            trust: values.remember ?? false
          }).then((response) => {
            handleSuccessFullAuth(response, navigate, location, setError);
          });
          return true;
        }
      } else {
        const errors = err.response?.data?.errors;
        let msg = t`An error occurred`;

        if (errors) {
          msg = errors.map((e: any) => e.message).join(', ');
        }
        setError(msg);
      }
      return false;
    });
}

/**
 * Check login state, and redirect the user as required.
 *
 * The user may be logged in via the following methods:
 * - An existing API token is stored in the session
 * - An existing CSRF cookie is stored in the browser
 */
export const checkLoginState = async (
  navigate: NavigateFunction,
  redirect?: any,
  no_redirect?: boolean
) => {
  const { setLoginChecked } = useUserState.getState();
  setApiDefaults();

  if (redirect == '/') {
    redirect = '/home';
  }

  const { isLoggedIn, fetchUserState } = useUserState.getState();

  // Callback function when login is successful
  const loginSuccess = async () => {
    setLoginChecked(true);
    showLoginNotification({
      title: t`Logged In`,
      message: t`Successfully logged in`
    });
    MfaSetupOk(navigate).then(async (isOk) => {
      if (isOk) {
        observeProfile();
        await fetchGlobalStates();

        followRedirect(navigate, redirect);
      }
    });
  };

  if (isLoggedIn()) {
    // Already logged in
    await loginSuccess();
    return;
  }

  // Not yet logged in, but we might have a valid session cookie
  // Attempt to login
  await fetchUserState();

  if (isLoggedIn()) {
    await loginSuccess();
  } else if (!no_redirect) {
    setLoginChecked(true);
    navigate('/login', { state: redirect });
  }
  setLoginChecked(true);
};

function handleSuccessFullAuth(
  response: any,
  navigate: NavigateFunction,
  location?: Location<any>,
  setError?: (message: string | undefined) => void
) {
  const { setAuthenticated, fetchUserState } = useUserState.getState();
  const { setAuthContext } = useServerApiState.getState();

  if (setError) {
    // If an error function is provided, clear any previous errors
    setError(undefined);
  }

  if (response.data?.data) {
    setAuthContext(response.data?.data);
  }
  setAuthenticated();

  // see if mfa registration is required
  MfaSetupOk(navigate).then(async (isOk) => {
    if (isOk) {
      await fetchUserState();
      observeProfile();
      await fetchGlobalStates();

      if (location !== undefined) {
        followRedirect(navigate, location?.state);
      }
    }
  });
}

/*
 * Return the value of the CSRF cookie, if available
 */
export function getCsrfCookie() {
  const cookieValue = document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrftoken='))
    ?.split('=')[1];

  return cookieValue;
}

/*
 * Clear out the CSRF and session cookies (force session logout)
 */
export function clearCsrfCookie() {
  document.cookie =
    'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
}

export async function ProviderLogin(
  provider: AuthProvider,
  process: 'login' | 'connect' = 'login'
) {
  await ensureCsrf();
  post(generateUrl(apiUrl(ApiEndpoints.auth_provider_redirect)), {
    provider: provider.id,
    callback_url: generateUrl('/logged-in'),
    process: process,
    csrfmiddlewaretoken: getCsrfCookie()
  });
}

/**
 * Makes an API request with session tokens using the provided URL, configuration, method, and data.
 *
 * @param url - The URL to which the request is sent.
 * @param config - Optional Axios request configuration.
 * @param method - The HTTP method to use for the request. Defaults to 'get'.
 * @param data - Optional data to be sent with the request.
 * @returns A promise that resolves to the response of the API request.
 */
export function authApi(
  url: string,
  config: AxiosRequestConfig | undefined = undefined,
  method: 'get' | 'patch' | 'post' | 'put' | 'delete' = 'get',
  data?: any
) {
  const requestConfig = config || {};

  // set method
  requestConfig.method = method;

  // set data
  if (data) {
    requestConfig.data = data;
  }

  // use normal api
  return api(url, requestConfig);
}

export const getTotpSecret = async (setTotpQr: any) => {
  await authApi(apiUrl(ApiEndpoints.auth_totp), undefined, 'get').catch(
    (err) => {
      if (err.status == 404 && err.response.data.meta.secret) {
        setTotpQr(err.response.data.meta);
      } else {
        const msg = err.response.data.errors[0].message;
        showNotification({
          title: t`Failed to set up MFA`,
          message: msg,
          color: 'red'
        });
      }
    }
  );
};

export function handleVerifyTotp(
  value: string,
  navigate: NavigateFunction,
  location: Location<any>
) {
  return () => {
    authApi(apiUrl(ApiEndpoints.auth_totp), undefined, 'post', {
      code: value
    }).then(() => {
      showNotification({
        title: t`MFA Setup successful`,
        message: t`MFA via TOTP has been set up successfully; you will need to login again.`,
        color: 'green'
      });
      doLogout(navigate);
    });
  };
}

export function handlePasswordReset(
  key: string | null,
  password: string,
  navigate: NavigateFunction
) {
  function success() {
    notifications.show({
      title: t`Password set`,
      message: t`The password was set successfully. You can now login with your new password`,
      color: 'green',
      autoClose: false
    });
    navigate('/login');
  }

  function passwordError(values: any) {
    notifications.show({
      title: t`Reset failed`,
      message: values?.errors.map((e: any) => e.message).join('\n'),
      color: 'red'
    });
  }

  // Set password with call to backend
  api
    .post(
      apiUrl(ApiEndpoints.user_reset_set),
      {
        key: key,
        password: password
      },
      { headers: { Authorization: '' } }
    )
    .then((val) => {
      if (val.status === 200) {
        success();
      } else {
        passwordError(val.data);
      }
    })
    .catch((err) => {
      if (err.response?.status === 400) {
        passwordError(err.response.data);
      } else if (err.response?.status === 401) {
        success();
      } else {
        passwordError(err.response.data);
      }
    });
}

export function handleVerifyEmail(
  key: string | undefined,
  navigate: NavigateFunction
) {
  // Set password with call to backend
  api
    .post(apiUrl(ApiEndpoints.auth_email_verify), {
      key: key
    })
    .then((val) => {
      if (val.status === 200) {
        navigate('/login');
      }
    });
}

export function handleChangePassword(
  pwd1: string,
  pwd2: string,
  current: string,
  navigate: NavigateFunction
) {
  const { clearUserState } = useUserState.getState();

  function passwordError(values: any) {
    let message: any =
      values?.new_password ||
      values?.new_password2 ||
      values?.new_password1 ||
      values?.current_password ||
      values?.error ||
      t`Password could not be changed`;

    // If message is array
    if (!Array.isArray(message)) {
      message = [message];
    }

    message.forEach((msg: string) => {
      notifications.show({
        title: t`Error`,
        message: msg,
        color: 'red'
      });
    });
  }

  // check if passwords match
  if (pwd1 !== pwd2) {
    passwordError({ new_password2: t`The two password fields didn’t match` });
    return;
  }

  // Set password with call to backend
  api
    .post(apiUrl(ApiEndpoints.auth_pwd_change), {
      current_password: current,
      new_password: pwd2
    })
    .then((val) => {
      passwordError(val.data);
    })
    .catch((err) => {
      if (err.status === 401) {
        notifications.show({
          title: t`Password Changed`,
          message: t`The password was set successfully. You can now login with your new password`,
          color: 'green',
          autoClose: false
        });
        clearUserState();
        clearCsrfCookie();
        navigate('/login');
      } else {
        // compile errors
        const errors: { [key: string]: string[] } = {};
        for (const val of err.response.data.errors) {
          if (!errors[val.param]) {
            errors[val.param] = [];
          }
          errors[val.param].push(val.message);
        }
        passwordError(errors);
      }
    });
}

export async function handleWebauthnLogin(
  navigate: NavigateFunction,
  location: Location<any>
) {
  const { setAuthContext } = useServerApiState.getState();

  const webauthn_challenge = await api
    .get(apiUrl(ApiEndpoints.auth_webauthn_login))
    .catch(() => {})
    .then((response) => {
      if (response && response.status === 200) {
        return response.data.data.request_options;
      }
    });

  if (!webauthn_challenge) {
    return;
  }

  try {
    const credential = await get(
      parseRequestOptionsFromJSON(
        webauthn_challenge as CredentialRequestOptionsJSON
      )
    );
    await api
      .post(apiUrl(ApiEndpoints.auth_webauthn_login), {
        credential: credential
      })
      .then((response) => {
        if (response.status === 200) {
          handleSuccessFullAuth(response, navigate, location, undefined);
        }
      })
      .catch((err) => {
        if (err?.response?.status == 401) {
          const mfa_trust = err.response.data.data.flows.find(
            (flow: any) => flow.id == FlowEnum.MfaTrust
          );
          if (mfa_trust?.is_pending) {
            setAuthContext(err.response.data.data);
            authApi(apiUrl(ApiEndpoints.auth_trust), undefined, 'post', {
              trust: false
            }).then((response) => {
              handleSuccessFullAuth(response, navigate, location, undefined);
            });
          }
        }
      });
  } catch (e) {
    console.error(e);
  }
}
