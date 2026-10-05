/* Fixed paginated People GETs through the already-loaded website SDK. */
async function probeBreezeV2People() {
  const moduleUrl = 'https://main.ddgv4rlrmu56c.amplifyapp.com/assets/main-BkBiSYb4.js';
  const loaded = Array.from(document.querySelectorAll('script[src]'), e => e.src)
    .concat(performance.getEntriesByType('resource').map(e => e.name));
  if (!loaded.includes(moduleUrl)) return JSON.stringify({state: 'module_not_loaded'});
  const samples = [];
  const rows = [];
  try {
    const frontend = await import(moduleUrl);
    if (typeof frontend.a !== 'function') return JSON.stringify({state: 'sdk_contract_changed', stage: 'factory_export', factory_type: typeof frontend.a});
    const client = frontend.a('https://api.breezechms.com/api/v2');
    if (typeof client?.people?.getPeople !== 'function') return JSON.stringify({state: 'sdk_contract_changed', stage: 'people_service',
      candidate_types: Object.fromEntries(['people','api','client','request'].map(key => [key, typeof client?.[key]]))});
    for (const page of [0, 1, 2]) {
      const body = await client.people.getPeople({page, pageSize: 2, sort: 'id', noLimit: false});
      const data = Array.isArray(body) ? body :
        [body.data, body.people, body.results, body.items].find(Array.isArray);
      samples.push({page, schema: reduceBreezeSchema(body)});
      rows.push(data || null);
      if (!data || data.length > 2) return JSON.stringify({state: 'paging_not_verified', samples});
    }
    const ids = rows.map(page => page.map(row => row?.id));
    const comparable = ids.every(page => page.length && page.every(id => typeof id === 'string' || typeof id === 'number'));
    const sameFirst = comparable ? JSON.stringify(ids[0]) === JSON.stringify(ids[1]) : null;
    const disjoint = comparable ? ids[1].every(id => !ids[2].includes(id)) : null;
    return JSON.stringify({state: 'completed', samples, counts: rows.map(page => page.length),
      page_zero_matches_one: sameFirst, pages_one_two_disjoint: disjoint});
  } catch (error) {
    const status = Number.isInteger(error?.status) ? error.status : null;
    return JSON.stringify({state: status === 401 ? 'login_required' : status === 403 ? 'permission_denied' : 'request_failed',
      http_status: status, samples});
  }
}
