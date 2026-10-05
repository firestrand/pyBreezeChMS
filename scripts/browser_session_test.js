/* Fixed synthetic session checks; no real DOM, cookies or network access. */
(async () => {
  const location = {origin: 'https://demo.breezechms.com'};
  let passwords = [];
  const document = {querySelectorAll: () => passwords};
  const getComputedStyle = () => ({visibility: 'visible'});
  let calls = 0;
  let canceled = 0;
  let finalPath = '/dashboard';
  const fetch = async (url, options) => {
    if (url !== location.origin + '/dashboard' || options.method !== 'GET' ||
        options.credentials !== 'same-origin' || options.cache !== 'no-store') {
      throw Error('Synthetic request boundary failed');
    }
    calls++;
    return {ok: true, status: 200, url: location.origin + finalPath,
      body: {cancel: async () => {canceled++;}},
      text: () => {throw Error('Response body must not be read');}};
  };
  // SESSION_SCANNER
  const healthy = JSON.parse(await inspectBrowserSession(location.origin + '/dashboard'));
  finalPath = '/new-ui/dashboard';
  const redirected = JSON.parse(await inspectBrowserSession(location.origin + '/dashboard'));
  finalPath = '/login';
  const expired = JSON.parse(await inspectBrowserSession(location.origin + '/dashboard'));
  const rejected = JSON.parse(await inspectBrowserSession('https://evil.example/dashboard'));
  passwords = [{getClientRects: () => [1]}];
  const login = JSON.parse(await inspectBrowserSession(location.origin + '/dashboard'));
  passwords = [{getClientRects: () => []}];
  finalPath = '/dashboard';
  const hidden = JSON.parse(await inspectBrowserSession(location.origin + '/dashboard'));
  const checks = {
    authenticated_get_only: healthy.state === 'healthy',
    unread_bodies_canceled: canceled === calls,
    expiry_detected: expired.state === 'login_required',
    cross_origin_rejected: rejected.state === 'target_rejected',
    login_not_captured: login.state === 'login_required' && calls === 4,
    dashboard_redirect_supported: redirected.state === 'healthy',
    hidden_password_ignored: hidden.state === 'healthy'
  };
  return JSON.stringify({checks, passed: Object.values(checks).every(Boolean)});
})()
