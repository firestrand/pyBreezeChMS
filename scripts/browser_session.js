/* Fixed session liveness probe. Never read response bodies or credential values. */
async function inspectBrowserSession(dashboardUrl) {
  const visiblePassword = Array.from(document.querySelectorAll('input[type=password]'))
    .some(e => e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden');
  if (visiblePassword) return JSON.stringify({state: 'login_required'});
  const target = new URL(dashboardUrl);
  if (target.origin !== location.origin || target.username || target.password ||
      target.search || target.hash || !/^\/(?:[a-z0-9_-]+\/)?dashboard\/?$/i.test(target.pathname)) {
    return JSON.stringify({state: 'target_rejected'});
  }
  try {
    const response = await fetch(target.href, {
      method: 'GET', credentials: 'same-origin', cache: 'no-store',
      redirect: 'follow', signal: AbortSignal.timeout(10000)
    });
    if (response.body) await response.body.cancel();
    const final = new URL(response.url);
    const login = /\/(?:login|signin|logout)(?:\/|$)/i.test(final.pathname);
    const allowed = final.origin === location.origin &&
      /^\/(?:[a-z0-9_-]+\/)?dashboard\/?$/i.test(final.pathname);
    return JSON.stringify({
      state: login || response.status === 401 ? 'login_required' :
        response.ok && allowed ? 'healthy' : 'request_failed',
      http_status: response.status
    });
  } catch {
    return JSON.stringify({state: 'request_failed'});
  }
}
