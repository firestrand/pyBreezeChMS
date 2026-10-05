/* Fixed reviewed People reads through the website's existing session setup. */
async function probeBreezePeople() {
  if (typeof jQuery === 'undefined' || typeof jQuery.ajax !== 'function') {
    return JSON.stringify({state: 'jquery_unavailable'});
  }
  const bodies = [];
  const samples = [];
  for (const limit of [2, 3]) {
    const result = await new Promise(resolve => {
      jQuery.ajax({type: 'POST', url: '/ajax/list_all_people', data: {limit},
        dataType: 'text', timeout: 10000,
        success: (text, _status, xhr) => resolve({status: xhr.status, text}),
        error: xhr => resolve({status: xhr.status})});
    });
    const status = Number.isInteger(result.status) ? result.status : 0;
    if (typeof result.text !== 'string' || result.text.length > 2 * 1024 * 1024) {
      samples.push({limit, status, format: typeof result.text === 'string' ? 'too_large' : 'http_error'});
      break;
    }
    samples.push({limit, status, ...reduceBreezeBody(result.text)});
    try {
      const data = JSON.parse(result.text);
      const rows = Array.isArray(data) ? data :
        [data.data, data.people, data.results, data.items].find(Array.isArray);
      bodies.push(rows || null);
    } catch { bodies.push(null); }
  }
  const comparable = bodies.length === 2 && bodies.every(Array.isArray);
  const counts = comparable ? bodies.map(rows => Math.min(rows.length, 10000)) : [];
  const hasIds = comparable && bodies.every(rows => rows.slice(0, 2).every(row => row && Object.hasOwn(row, 'id')));
  const prefixStable = hasIds && bodies[0].length >= 2 && bodies[1].length >= 2 ?
    bodies[0].slice(0, 2).every((row, i) => row.id === bodies[1][i].id) : null;
  return JSON.stringify({state: 'completed', samples, array_counts: counts,
    limit_honored: comparable ? counts[0] <= 2 && counts[1] <= 3 : null,
    prefix_stable: prefixStable});
}
