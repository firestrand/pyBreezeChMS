/* Reduce legacy page code to request contracts; never return scripts or values. */
function inspectPageContracts() {
  const MAX_SCRIPT = 1024 * 1024;
  const identifier = /^[A-Za-z_$][A-Za-z0-9_$]{0,63}$/;
  const skipString = (s, i) => {
    const quote = s[i++];
    while (i < s.length) {
      if (s[i] === '\\') i += 2;
      else if (s[i++] === quote) return i;
    }
    return s.length;
  };
  const skipComment = (s, i) => {
    if (s.slice(i, i + 2) === '//') {
      const end = s.indexOf('\n', i + 2);
      return end < 0 ? s.length : end + 1;
    }
    if (s.slice(i, i + 2) === '/*') {
      const end = s.indexOf('*/', i + 2);
      return end < 0 ? s.length : end + 2;
    }
    return i;
  };
  const fields = (s, start) => {
    const found = {};
    let i = start + 1;
    for (let count = 0; count < 32 && i - start < 16000; count++) {
      while (/\s|,/.test(s[i] || '') && i < s.length) i++;
      const key = /^([A-Za-z_$][A-Za-z0-9_$]*)\s*:/.exec(s.slice(i));
      if (!key) break;
      i += key[0].length;
      const begin = i;
      const stack = [];
      while (i < s.length && i - start < 16000) {
        const c = s[i];
        if (c === '`') return found; // Computed templates are outside this parser.
        if (c === '"' || c === "'") { i = skipString(s, i); continue; }
        const after = skipComment(s, i);
        if (after !== i) { i = after; continue; }
        if (!stack.length && (c === ',' || c === '}')) break;
        if ('{[('.includes(c)) stack.push(c);
        else if ('}])'.includes(c)) {
          const open = stack.pop();
          if (!open || '{[('.indexOf(open) !== '}])'.indexOf(c)) return found;
        }
        i++;
      }
      if (i - start >= 16000) break;
      found[key[1]] = s.slice(begin, i).trim();
      if (key[1] === 'success' || key[1] === 'error' || s[i] === '}') break;
      i++;
    }
    return found;
  };
  const literal = value => {
    const match = /^(['"])([A-Za-z0-9_./-]+)\1$/.exec(value || '');
    return match ? match[2] : null;
  };
  const declarations = [];
  let truncated = false;
  const scripts = Array.from(document.querySelectorAll('script:not([src])'));
  for (const element of scripts.slice(0, 100)) {
    const source = element.textContent || '';
    if (source.length > MAX_SCRIPT) { truncated = true; continue; }
    let i = 0;
    while (i < source.length && declarations.length < 100) {
      if (['"', "'", '`'].includes(source[i])) { i = skipString(source, i); continue; }
      const after = skipComment(source, i);
      if (after !== i) { i = after; continue; }
      const match = /^(?:\$|jQuery)\.ajax\s*\(\s*\{/.exec(source.slice(i));
      if (!match) { i++; continue; }
      const options = fields(source, i + match[0].lastIndexOf('{'));
      const method = literal(options.type || options.method);
      const path = literal(options.url);
      const normalized = path?.replace(/^(?:\.\.\/|\.\/)+/, '/');
      if (method && /^(GET|POST)$/i.test(method) && normalized &&
          /^\/?ajax\/[a-z_]{1,80}$/.test(normalized)) {
        const data = options.data || '';
        const names = data.startsWith('{') ? Object.keys(fields(data, 0)) : [];
        declarations.push({method: method.toUpperCase(), route: '/' + normalized.replace(/^\//, ''),
          request_keys: names.filter(n => identifier.test(n)).sort(),
          computed_data: !data.startsWith('{') && !!data});
      }
      i += match[0].length;
    }
    if (declarations.length >= 100) { truncated = true; break; }
  }
  const contributionRequests = (globalThis.performance?.getEntriesByType('resource') || []).flatMap(entry => {
    try {
      const url = new URL(entry.name);
      if (url.origin !== 'https://api.breezechms.com' || url.pathname.replace(/\/{2,}/g,'/').replace(/\/$/,'') !== '/api/v2/contributions') return [];
      const keys = Array.from(url.searchParams.keys()).map(key => ['page','limit','pageSize','sort','filter','api','config','year','start_date','end_date','startDate','endDate'].includes(key) ? key : '{field}');
      return [{empty_path_segments: url.pathname.split('/').slice(1).filter(part => !part).length,query_keys: [...new Set(keys)].sort(),initiator: ['fetch','xmlhttprequest'].includes(entry.initiatorType) ? entry.initiatorType : 'other'}];
    } catch {return [];}
  }).slice(-20);
  const viewActions = Array.from(document.querySelectorAll('a[href]')).flatMap(a => {
    try {
      const url=new URL(a.href); if(url.origin!==location.origin)return [];
      const tokens=url.pathname.toLowerCase().split(/[\/_.-]/).filter(token=>['add','edit','import','installed','create','export','download','delete','send'].includes(token));
      return tokens.length ? [{tokens:[...new Set(tokens)],query_free:!url.search}] : [];
    } catch {return [];}
  }).slice(0,100);
  return JSON.stringify({declarations, truncated, inspected_script_count: Math.min(scripts.length, 100), contribution_requests: contributionRequests, view_actions: viewActions});
}
