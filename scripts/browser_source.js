/* Inspect static source as text. Never execute it or return source/record values. */
async function inspectBrowserSource(mode, index, dependency = null) {
  const MAX_BYTES = 12 * 1024 * 1024;
  const MAX_ROUTES = 700;
  const scriptUrls = Array.from(document.querySelectorAll('script[src]'), s => s.src);
  const resources = performance.getEntriesByType('resource');
  const breezeScriptOrigins = new Set(scriptUrls.flatMap(value => {
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && url.hostname.endsWith('.breezechms.com') &&
        !url.username && !url.password && Array.from(url.searchParams.keys()).every(key => ['_', 'v', 'version'].includes(key)) ? [url.origin] : [];
    } catch {return [];}
  }));
  const sourceOriginAllowed = url => url.protocol === 'https:' &&
    (url.origin === location.origin || ['https://main.ddgv4rlrmu56c.amplifyapp.com', 'https://app.breezechms.com'].includes(url.origin) || breezeScriptOrigins.has(url.origin));
  const extensionless = value => {
    try {
      const url = new URL(value);
      const observedScript = scriptUrls.includes(value) || resources.some(e => e.name === value && ['script', 'xmlhttprequest'].includes(e.initiatorType));
      return observedScript && /^\/js\/(?:[A-Za-z0-9_-]+\/){0,8}[A-Za-z0-9_-]+$/.test(url.pathname) &&
        Array.from(url.searchParams.keys()).every(key => ['_', 'v', 'version'].includes(key));
    } catch { return false; }
  };
  const candidates = Array.from(new Set([
    ...scriptUrls,
    ...resources.map(e => e.name)
  ]));
  const eligible = candidates.filter(value => {
    try {
      const url = new URL(value);
      return sourceOriginAllowed(url) &&
        /^\/(?:js|assets|static|v[1-9]|dist|build)\//.test(url.pathname) &&
        (/\.(?:m?js)$/.test(url.pathname) || extensionless(value)) && !url.username && !url.password &&
        Array.from(url.searchParams.keys()).every(key => ['_', 'v', 'version'].includes(key));
    } catch { return false; }
  }).sort();
  const cacheKey = Symbol.for('breezeInspectionAssets');
  const urls = globalThis[cacheKey] || (globalThis[cacheKey] = []);
  for (const value of eligible) if (!urls.includes(value)) urls.push(value);
  // Asset URLs never leave the browser; indices select from the current page.
  if (mode === 'assets') {
    const breezeScriptLocations = scriptUrls.flatMap(value => {
      try {
        const url = new URL(value);
        if (!url.hostname.endsWith('.breezechms.com')) return [];
        const host = url.origin === location.origin ? 'account' :
          ['app','api','cdn','static','r','assets','js','www','app2','appv2','v2','legacy'].includes(url.hostname.split('.')[0]) ? url.hostname.split('.')[0] : 'other_breeze';
        return [{host_kind:host,root:['js','assets','static','dist','build','v2'].includes(url.pathname.split('/')[1])?url.pathname.split('/')[1]:'other',
          filename:/^[A-Za-z0-9_.-]{1,180}\.m?js$/.test(url.pathname.split('/').at(-1))?url.pathname.split('/').at(-1):'{asset}',eligible:eligible.includes(value)}];
      } catch {return [];}
    }).slice(0,100);
    const classes = {};
    const scriptSuffixes = {};
    const dynamicScriptShapes = resources.flatMap(e => {
      try {
        const url = new URL(e.name);
        if (!url.pathname.startsWith('/js/') || /\.m?js$/.test(url.pathname)) return [];
        const suffix = /\.([a-z]{1,8})$/.exec(url.pathname)?.[1] || 'none';
        return [{initiator: ['script', 'xmlhttprequest', 'fetch'].includes(e.initiatorType) ? e.initiatorType : 'other',
          segments: url.pathname.split('/').filter(Boolean).length, has_dots: url.pathname.includes('.'),
          suffix: ['php', 'none'].includes(suffix) ? suffix : 'other',
          query_keys: Array.from(url.searchParams.keys()).map(k => ['_', 'v', 'version'].includes(k) ? k : '{field}')}];
      } catch { return []; }
    }).slice(0, 30);
    for (const value of scriptUrls) {
      try {
        const suffix = /\.([a-z]{1,8})$/.exec(new URL(value).pathname)?.[1] || 'none';
        const key = ['js', 'mjs', 'php', 'none'].includes(suffix) ? suffix : 'other';
        scriptSuffixes[key] = (scriptSuffixes[key] || 0) + 1;
      } catch { /* Invalid script URLs are excluded. */ }
    }
    for (const value of candidates) {
      try {
        const url = new URL(value);
        const host = url.origin === location.origin ? 'same_origin' : url.hostname.endsWith('.breezechms.com') ? 'breeze_external' : 'third_party';
        const prefix = url.pathname.split('/')[1];
        const root = ['js', 'assets', 'static', 'dist', 'build'].includes(prefix) ? prefix : 'other';
        const suffix = /\.([a-z]{1,8})$/.exec(url.pathname)?.[1] || 'other';
        const key = host + ':' + root + ':' + suffix;
        classes[key] = (classes[key] || 0) + 1;
      } catch { /* Invalid URLs are excluded. */ }
    }
    const publicHosts = Array.from(new Set(candidates.map(value => {
      try {
        const url = new URL(value);
        return url.origin !== location.origin && (!url.hostname.endsWith('.breezechms.com') || /^(?:cdn|static|assets|app)\.breezechms\.com$/.test(url.hostname)) && /\.m?js$/.test(url.pathname) ? url.hostname : null;
      } catch { return null; }
    }).filter(Boolean))).sort();
    return JSON.stringify({assets: urls.map((url, i) => {
      const filename = new URL(url).pathname.split('/').at(-1);
      return {index: i, filename: /^[A-Za-z0-9_.-]{1,180}\.m?js$/.test(filename) ? filename : '{asset}', extensionless: extensionless(url)};
    }), count: urls.length, classes, script_suffixes: scriptSuffixes, dynamic_script_shapes: dynamicScriptShapes, public_asset_hosts: publicHosts,breeze_script_locations:breezeScriptLocations});
  }
  if (!Number.isInteger(index) || index < 0 || index >= urls.length) {
    return JSON.stringify({error: 'asset_unavailable'});
  }
  const identifier = value => /^[A-Za-z_$][A-Za-z0-9_$]{0,63}$/.test(value) ? value : '{identifier}';
  const route = value => value.replace(/^(?:\.\.\/|\.\/)+(?=ajax\/|api\/)/, '/').split(/[?#]/)[0].split('/').map(part => {
    if (!part) return '';
    if (/^[a-z][a-z0-9_.-]{0,79}$/.test(part) && !/[a-f0-9]{20,}/.test(part)) return part;
    return '{segment}';
  }).join('/');
  const analyze = async text => {
    const references = [];
    const declarations = [];
    const expression = /(["'`])((?:(?:\.\.\/|\.\/)*(?:ajax|api)\/|\/(?!\/)|contributions(?:\/|(?=[?"'`])))[^"'`]{0,200})\1/g;
    let match;
    while ((match = expression.exec(text)) !== null && references.length < MAX_ROUTES) {
      const start = match.index;
      if (/\.(?:js|css|svg|png|jpg|woff2?)(?:[?#]|$)/.test(match[2])) continue;
      const nearby = text.slice(Math.max(0, start - 500), start + match[0].length + 700);
      const prefix = text.slice(Math.max(0, start - 120), start);
      const declared = /method\s*:\s*["'](GET|POST|PUT|PATCH|DELETE|HEAD)["']\s*,\s*url\s*:\s*$/i.exec(prefix);
      const direct = /([A-Za-z_$][A-Za-z0-9_$]*)\.(get|post|put|patch|delete)\s*\(\s*$/i.exec(prefix);
      const argumentCall = /\(\s*["'](GET|POST|PUT|PATCH|DELETE|HEAD)["']\s*,\s*$/i.exec(prefix);
      if (declared || direct || argumentCall) {
        const after = text.slice(start + match[0].length, start + match[0].length + 1800);
        const query = /^\s*,\s*(?:path\s*:\s*\{[^}]*\}\s*,\s*)?query\s*:\s*\{([^}]*)\}/.exec(after);
        const body = direct ? /^\s*,\s*\{([^}]{0,1000})\}/.exec(after) : null;
        const names = part => part ? Array.from(part.matchAll(/(?:^|,)\s*(?:["']([A-Za-z_$][A-Za-z0-9_$]*)["']|([A-Za-z_$][A-Za-z0-9_$]*))\s*:/g), m => identifier(m[1] || m[2])).sort() : [];
        const methodNames = Array.from(text.slice(Math.max(0, start - 600), start).matchAll(/\bstatic\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(/g));
        const methodName = methodNames.at(-1);
        declarations.push({route: route(match[2]), method: declared ? declared[1].toUpperCase() : direct ? direct[2].toUpperCase() : argumentCall[1].toUpperCase(), query_keys: names(query?.[1]), body_keys: names(body?.[1]), client_symbol: direct ? identifier(direct[1]) : null, sdk_method: methodName ? identifier(methodName[1]) : null});
      }
      const methods = new Set();
      for (const m of nearby.matchAll(/(?:method|type)\s*:\s*["'](GET|POST|PUT|PATCH|DELETE|HEAD)["']/gi)) methods.add(m[1].toUpperCase());
      for (const m of text.slice(Math.max(0, start - 80), start).matchAll(/\.(get|post|put|patch|delete)\s*\(\s*$/gi)) methods.add(m[1].toUpperCase());
      const keys = new Set();
      for (const m of nearby.matchAll(/(?:["']([A-Za-z_$][A-Za-z0-9_$]*)["']|\b([A-Za-z_$][A-Za-z0-9_$]*))\s*:/g)) keys.add(identifier(m[1] || m[2]));
      const before = text.slice(Math.max(0, start - 2000), start);
      const functions = Array.from(before.matchAll(/(?:function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(|(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s*)?(?:function|\([^)]{0,200}\)\s*=>))/g));
      const last = functions.at(-1);
      const literalQueryKeys=Array.from(new URLSearchParams(match[2].split('?')[1]||'').keys()).filter(key=>/^[A-Za-z_][A-Za-z0-9_\[\]>=<:. -]{0,120}$/.test(key)).slice(0,30);
      references.push({literal_query_keys:literalQueryKeys,route: route(match[2]), nearby_methods: [...methods].sort(), nearby_property_names: [...keys].sort().slice(0, 50), preceding_function: last ? identifier(last[1] || last[2]) : null});
    }
    const markers = {};
    for (const key of ['csrf', 'xsrf', 'Authorization', 'Bearer', 'withCredentials', 'credentials', 'oauth', 'openid', 'code_challenge', 'client_id', 'redirect_uri', 'api_key', 'localStorage', 'sessionStorage', 'accessToken', 'refreshToken', 'expiresIn', 'sessionKey', 'breezeToken', 'page', 'per_page', 'page_size', 'offset', 'limit', 'cursor', 'next_page', 'total_pages', 'has_more', 'serverSide', 'draw', 'export', 'download', 'graphql']) {
      const hits = text.match(new RegExp('\\b' + key + '\\b', 'gi'));
      if (hits) markers[key] = hits.length;
    }
    const grantTypes = Array.from(new Set(Array.from(text.matchAll(/grant_type\s*:\s*["'](authorization_code|refresh_token|client_credentials|session_token|password)["']/g), m => m[1]))).sort();
    const storageKeys = Array.from(new Set(Array.from(text.matchAll(/(?:localStorage|sessionStorage)\.(?:getItem|setItem|removeItem)\(\s*["']([A-Za-z_][A-Za-z0-9_]{0,63})["']/g), m => m[1]))).sort();
    const authCalls = Array.from(new Set(Array.from(text.matchAll(/\.([A-Za-z_$][A-Za-z0-9_$]{0,63})\s*\(/g), m => m[1]).filter(name => /oauth|auth|login|token/i.test(name)))).sort();
    const serviceUrls = [];
    for (const m of text.matchAll(/["'`](https:\/\/[^"'`\s<>]{1,200})["'`]/g)) {
      try {
        const url = new URL(m[1]);
        if (/^(?:api|auth|accounts|login|id|identity|sso)\.(?:tithe\.ly|tithely\.com|breezechms\.com)$/.test(url.hostname)) {
          const before = text.slice(Math.max(0, m.index - 160), m.index);
          const property = /([A-Za-z_$][A-Za-z0-9_$]*)\s*:\s*$/.exec(before);
          const assigned = /([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:(?:new\s+)?[A-Za-z_$][A-Za-z0-9_$]*\s*\(\s*)?$/.exec(before);
          const client = /([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*[A-Za-z_$][A-Za-z0-9_$]*\.create\(\{baseURL\s*:\s*$/.exec(before);
          serviceUrls.push({host: url.hostname, path: route(url.pathname), property: property ? identifier(property[1]) : null, assigned_symbol: assigned ? identifier(assigned[1]) : null, client_symbol: client ? identifier(client[1]) : null});
        }
      } catch { /* Dynamic templates are not origins. */ }
    }
    const bytes = new TextEncoder().encode(text);
    const digest = await crypto.subtle.digest('SHA-256', bytes);
    const sha256 = Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('');
    const imports = Array.from(new Set(Array.from(text.matchAll(/["']((?:\.\/)?(?:assets\/)?[A-Za-z0-9_.-]{1,150}\.m?js)["']/g), m => m[1]))).sort();
    const clients = Array.from(text.matchAll(/([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*[A-Za-z_$][A-Za-z0-9_$]*\.create\(\{\s*baseURL\s*:\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*[,}]/g), m => ({client_symbol: identifier(m[1]), base_symbol: identifier(m[2])}));
    const parameterKeys = new Set();
    const wrapperShapes = Array.from(text.matchAll(/params\s*:\s*\{api\s*:/g), m => {
      const expression=text.slice(m.index+m[0].length,m.index+500).replace(/(["'`])(?:\\.|(?!\1)[\s\S])*?\1/g,'"{literal}"');
      return {api_value_form:/^\s*JSON\.stringify\(/.test(expression)?'json_stringify':/^\s*\{/.test(expression)?'object':/^\s*[A-Za-z_$][A-Za-z0-9_$]*[},]/.test(expression)?'identifier':'other',
        property_names:[...new Set(Array.from(expression.matchAll(/\.([A-Za-z_$][A-Za-z0-9_$]{0,63})/g), p=>identifier(p[1])))].slice(0,30),
        function_names:[...new Set(Array.from(expression.matchAll(/\b([A-Za-z_$][A-Za-z0-9_$]{0,63})\(/g), p=>identifier(p[1])))].slice(0,30)};
    }).slice(0,10);
    for (const params of text.matchAll(/params\s*:\s*\{([^}]{0,1600})\}/g)) {
      for (const key of params[1].matchAll(/(?:^|,)\s*(?:["']([A-Za-z_$][A-Za-z0-9_$]*)["']|([A-Za-z_$][A-Za-z0-9_$]*))\s*:/g)) parameterKeys.add(identifier(key[1]||key[2]));
    }
    return {index, dependency, bytes: bytes.length, sha256, references, declarations, markers, grant_types: grantTypes, auth_call_names: authCalls.slice(0, 100), storage_key_names: storageKeys, service_urls: serviceUrls.slice(0, 40), http_client_definitions: clients.slice(0, 40), import_paths: imports.slice(0, 1000), request_wrapper_shapes:wrapperShapes, parameter_key_names:[...parameterKeys].sort().slice(0,100), truncated: references.length === MAX_ROUTES};
  };
  try {
    const read = async url => {
    const target = new URL(url);
    if (!sourceOriginAllowed(target) ||
        !/^\/(?:js|assets|static|v[1-9]|dist|build)\//.test(target.pathname) ||
        !(/\.m?js$/.test(target.pathname) || extensionless(url)) || target.username || target.password ||
        !Array.from(target.searchParams.keys()).every(key => ['_', 'v', 'version'].includes(key))) {
      return JSON.stringify({index, error: 'asset_location_refused'});
    }
    const response = await fetch(url, {method: 'GET', credentials: 'omit', redirect: 'error', signal: AbortSignal.timeout(10000), cache: 'force-cache'});
    if (!response.ok) return JSON.stringify({index, error: 'asset_fetch_failed', status: response.status});
    if (!(extensionless(url) ? /(?:javascript|ecmascript)/i : /(?:javascript|ecmascript|text\/plain|octet-stream)/i).test(response.headers.get('content-type') || '')) return JSON.stringify({index, error: 'asset_type_refused'});
    if (!response.body) return JSON.stringify({index, error: 'asset_body_unavailable'});
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const chunks = [];
    let bytes = 0;
    while (true) {
      const item = await reader.read();
      if (item.done) break;
      bytes += item.value.length;
      if (bytes > MAX_BYTES) { await reader.cancel(); return JSON.stringify({index, error: 'asset_too_large'}); }
      chunks.push(decoder.decode(item.value, {stream: true}));
    }
    chunks.push(decoder.decode());
    return chunks.join('');
    };
    const text = await read(urls[index]);
    // Errors from read are fixed JSON strings, never the body of a failed fetch.
    if (text.startsWith('{"index":')) return text;
    const result = await analyze(text);
    if (dependency === null) return JSON.stringify(result);
    if (!Number.isInteger(dependency) || dependency < 0 || dependency >= result.import_paths.length) return JSON.stringify({error: 'dependency_unavailable'});
    const assetUrl = new URL(urls[index]);
    const name = result.import_paths[dependency];
    const selected = new URL(name.startsWith('assets/') ? '/' + name : name, assetUrl);
    if (selected.origin !== assetUrl.origin || !/^\/(?:js|assets|static|v[1-9]|dist|build)\//.test(selected.pathname)) return JSON.stringify({error: 'dependency_refused'});
    const child = await read(selected.href);
    if (child.startsWith('{"index":')) return child;
    return JSON.stringify(await analyze(child));
  } catch { return JSON.stringify({index, error: 'asset_inspection_failed'}); }
}
