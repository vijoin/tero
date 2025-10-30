import { HttpError, ApiService } from "@/services/api";

export const handleOAuthRequestsIn = async <T>(fn: () => Promise<T>, api: ApiService) : Promise<T> => {
  while (true) {
    try {
      return await fn()
    } catch (e) {
      const oauthRequest = parseOAuthRequest(e);
      if (oauthRequest) {
        await oauthPopupFlow(oauthRequest, api);
      } else {
        throw e;
      }
    }
  }
}

const parseOAuthRequest = (e: unknown) : {url: string, state: string} | undefined => {
  if (!(e instanceof HttpError && e.status === 401 && e.body)) {
    return undefined
  }
  try {
    const body = JSON.parse(e.body);
    if (!body.detail) {
      return undefined
    }
    return new OAuthRequest(body.detail?.oauthUrl, body.detail?.oauthState);
  } catch (_) {
    return undefined
  }
}

class OAuthRequest {
  url: string
  state: string

  constructor(url: string, state: string) {
    this.url = url;
    this.state = state;
  }
}

export class AuthenticationWindowCloseError extends Error {
  constructor() {
    super('Authentication window closed');
  }
}

export class AuthenticationCancelError extends Error {
  constructor() {
    super('Authentication cancelled');
  }
}

const oauthPopupFlow = async (oauthRequest: OAuthRequest, api: ApiService) : Promise<void> => {
  return new Promise((resolve, reject) => {
    const popupWidth = 600;
    const popupHeight = 600;
    const left = window.screenX + (window.outerWidth - popupWidth) / 2;
    const top = window.screenY + (window.outerHeight - popupHeight) / 2;
    const popup = window.open(oauthRequest.url, 'OAuth', `popup,width=${popupWidth},height=${popupHeight},left=${left},top=${top}`);
    if (!popup) {
      reject(new Error('Failed to open popup'));
      return;
    }

    const checkClosed = setInterval(() => {
      if (popup.closed) {
        clearInterval(checkClosed);
        reject(new AuthenticationWindowCloseError());
      }
    }, 1000);

    const handleCallback = async (event: MessageEvent) => {
      if (!event.origin.startsWith(window.location.origin)) {
        return;
      }

      const data = event.data;
      if (data.type === 'oauth_callback' && data.state === oauthRequest.state) {
        try {
          window.removeEventListener('message', handleCallback);
          clearInterval(checkClosed);
          await api.toolAuth(data.toolId, data.code, data.state);
          resolve()
        } catch (error) {
          if (error instanceof HttpError && error.status === 400) {
            try {
              const body = JSON.parse(error.body);
              if (body.detail && body.detail === "Authentication cancelled") {
                reject(new AuthenticationCancelError());
                popup.close();
                return
              }
            } catch (_) {
            }
          }
          reject(error);
        }
        popup.close();
      }

    };

    window.addEventListener('message', handleCallback);
  });
}

