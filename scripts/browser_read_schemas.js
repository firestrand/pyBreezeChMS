/* Observe reviewed website reads. Raw responses remain inside browser memory. */
const BREEZE_API_READ_PATTERNS = [
  "/api/v2/attachments",
  "/api/v2/contributions/funds",
  "/api/v2/contributions",
  "/api/v2/contributions/overview",
  "/api/v2/contributions/batches",
  "/api/v2/contributions/funds/folders",
  "/api/v2/contributions/methods",
  "/api/v2/contributions/funds/{id}",
  "/api/v2/contributions/has-subscriptions",
  "/api/v2/emails/history",
  "/api/v2/emails/history/{id}",
  "/api/v2/emails/history/{id}/responses",
  "/api/v2/event-instances",
  "/api/v2/event-instances/{id}",
  "/api/v2/event-instances/{id}/people",
  "/api/v2/events/calendars",
  "/api/v2/events/calendars/{calendarIds}/embed",
  "/api/v2/events/external/{id}",
  "/api/v2/events/{eventId}/tags/{id}",
  "/api/v2/events/{id}",
  "/api/v2/events/{id}/tags",
  "/api/v2/features",
  "/api/v2/features/{id}",
  "/api/v2/followups/options",
  "/api/v2/groups",
  "/api/v2/groups/group-membership",
  "/api/v2/groups/{id}",
  "/api/v2/history/texts",
  "/api/v2/history/texts/{id}",
  "/api/v2/history/{type}",
  "/api/v2/integrations",
  "/api/v2/integrations/{id}",
  "/api/v2/me",
  "/api/v2/me/groups",
  "/api/v2/message-templates",
  "/api/v2/message-templates/{id}",
  "/api/v2/messages",
  "/api/v2/messages/{id}",
  "/api/v2/notifications",
  "/api/v2/organizations/info/{subdomain}",
  "/api/v2/people",
  "/api/v2/people/archive",
  "/api/v2/people/export-config",
  "/api/v2/people/search",
  "/api/v2/people/{id}",
  "/api/v2/people/{id}/address",
  "/api/v2/people/{id}/birthdate",
  "/api/v2/people/{id}/email",
  "/api/v2/people/{id}/name",
  "/api/v2/people/{id}/phone",
  "/api/v2/people/{person}/notes",
  "/api/v2/people/{person}/notes/{note}",
  "/api/v2/preferences",
  "/api/v2/preferences/{identifier}",
  "/api/v2/profile-merges",
  "/api/v2/profile-merges/{id}",
  "/api/v2/profilefields",
  "/api/v2/roles",
  "/api/v2/roles/{id}",
  "/api/v2/savedsearches",
  "/api/v2/savedsearches/{id}",
  "/api/v2/service-plan-templates",
  "/api/v2/service-plan-templates/{id}",
  "/api/v2/service-plans/{id}",
  "/api/v2/service-plans/{planId}/segments/{id}",
  "/api/v2/sms/enrollment-status",
  "/api/v2/song-library/instruments",
  "/api/v2/song-library/search",
  "/api/v2/song-library/song-select/{ccliNumber}",
  "/api/v2/song-library/song-versions",
  "/api/v2/song-library/songs",
  "/api/v2/song-library/songs/{id}",
  "/api/v2/song-library/songs/{songId}/versions/{id}",
  "/api/v2/song-library/songs/{songId}/versions/{id}/capo",
  "/api/v2/song-library/songs/{songId}/versions/{id}/chord-pro",
  "/api/v2/song-library/songs/{songId}/versions/{id}/chord-sheet",
  "/api/v2/song-library/songs/{songId}/versions/{id}/lyrics",
  "/api/v2/song-library/songtags",
  "/api/v2/song-library/team",
  "/api/v2/song-library/themes",
  "/api/v2/tags",
  "/api/v2/tags/folders",
  "/api/v2/tags/folders/{id}",
  "/api/v2/tags/people/{id}",
  "/api/v2/tags/{id}",
  "/api/v2/texts/limit",
  "/api/v2/texts/price",
  "/api/v2/texts/sent",
  "/api/v2/users",
  "/api/v2/users/fields",
  "/api/v2/users/{id}"
];
const BREEZE_SCHEMA_FIELDS = new Set([
  'id','name','first_name','last_name','email','phone','address','city','state','zip',
  'data','results','items','people','forms','folders','entries','fields','tags','funds',
  'folder_id','parent_id','form_id','person_id','field_id','value','type','status',
  'html','content','title','description','total','total_count','count','page','pageSize',
  'per_page','limit','offset','next','next_page','previous','last_page','current_page',
  'has_more','pagination','meta','links','created_at','updated_at','date','amount',
  'currency','fund_id','event_id','start','end','calendars','event_instances',
  'options','sort','order','search','query','filters','filter','ascending','archive','view',
  'sort_by','sort_type','view_type','show_archived','form_folder_id','q','text',
  'start_date','end_date','startDate','endDate','paid_on','from','to','after','before','min','max','paid_after','paid_before','starts_on','ends_on','gte','gt','lte','lt','ne','in','like','contains','between','created_on','check_number','is_anonymous','field','operator','operation','comparison','details','field_type','response','config','api','params','eq','batch_id','method','note','num','year'
]);
function reduceBreezeSchema(value, depth = 0, field = '', paging = false) {
  if (value === null) return {type: 'null'};
  if (Array.isArray(value)) return {type: 'array', count: Math.min(value.length, 10000),
    samples: depth < 4 ? value.slice(0, 3).map(v => reduceBreezeSchema(v, depth + 1, '', paging)) : []};
  if (typeof value === 'object') {
    const keys = Object.keys(value);
    const approved = keys.filter(k => BREEZE_SCHEMA_FIELDS.has(k)).slice(0, 64);
    const other = keys.filter(k => !BREEZE_SCHEMA_FIELDS.has(k));
    return {type: 'object', other_field_count: keys.length - approved.length,
      fields: depth < 4 ? Object.fromEntries(approved.map(k => [k, reduceBreezeSchema(value[k], depth + 1, k,
        paging && (typeof value[k] !== 'object' || ['options','config','api','meta','pagination'].includes(k)) ||
        depth === 0 && ['meta','pagination'].includes(k))])) : {},
      other_field_samples: depth < 4 ? other.slice(0, 3).map(k => reduceBreezeSchema(value[k], depth + 1)) : []};
  }
  if (paging && typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 &&
      ['total','total_count','count','page','pageSize','per_page','limit','offset','next_page','last_page','current_page'].includes(field)) {
    return {type: 'number', value: Math.min(value, 10000), bounded: value > 10000};
  }
  return {type: ['string', 'number', 'boolean'].includes(typeof value) ? typeof value : 'other'};
}
function reduceBreezeBody(text) {
  if (text.length > 2 * 1024 * 1024) return {format: 'too_large'};
  try { return {format: 'json', schema: reduceBreezeSchema(JSON.parse(text))}; }
  catch {
    return {format: /^\s*</.test(text) ? 'html' : 'other',
      tag_counts: Object.fromEntries(['tr','li','table','form'].map(tag => [tag,
        Math.min((text.match(new RegExp('<' + tag + '\\b', 'gi')) || []).length, 10000)]))};
  }
}
function redactFinancialMetadata(schema) {
  if (!schema || typeof schema !== 'object') return schema;
  if (schema.type === 'number') {delete schema.value;delete schema.bounded;}
  for (const child of Object.values(schema)) if (child && typeof child === 'object') redactFinancialMetadata(child);
  return schema;
}
function reduceBreezeRequest(body) {
  const values = {};
  let unrecognized = 0;
  const parameterShapes=[];
  const filterFieldIds=new Set();const filterOperatorIds=new Set();
  if (typeof body !== 'string' && !(body instanceof URLSearchParams)) return {type: 'unavailable'};
  for (const [key, value] of new URLSearchParams(body)) {
    const indexedFilter=/^(filter|filters)\[([0-9]{1,2})\]$/.exec(key);
    if(indexedFilter&&Number(indexedFilter[2])<64) {
      let parsed=value;try{parsed=JSON.parse(value);}catch{}
      if(!Array.isArray(values[indexedFilter[1]]))values[indexedFilter[1]]=[];
      values[indexedFilter[1]].push(parsed);
      const field=Array.isArray(parsed)?parsed[0]:parsed?.field;
      const operator=Array.isArray(parsed)?parsed[1]:parsed?.operator||parsed?.operation||parsed?.comparison;
      if(BREEZE_SCHEMA_FIELDS.has(field))filterFieldIds.add(field);
      if(['eq','ne','gt','gte','lt','lte','in','contains','like','between'].includes(operator))filterOperatorIds.add(operator);
      continue;
    }
    const nested = /^(options|config|api|filter|filters)((?:\[[A-Za-z_]+\]){1,4})$/.exec(key);
    const comparisonKey=/^(filter|filters)\[([A-Za-z_]+)[-_:.]{1,3}(eq|ne|gt|gte|lt|lte|in|like|contains|after|before|start|end|from|to|min|max)\]$/.exec(key);
    const fields = comparisonKey ? comparisonKey.slice(1) : nested ? [nested[1], ...Array.from(nested[2].matchAll(/\[([A-Za-z_]+)\]/g), m=>m[1])] : [key];
    if (!fields.every(field => BREEZE_SCHEMA_FIELDS.has(field))) { unrecognized++;if(parameterShapes.length<20)parameterShapes.push(key.split(/[\[\]]/).filter(Boolean).slice(0,6).map(field=>{field=field.trim();if(BREEZE_SCHEMA_FIELDS.has(field))return field;const comparison=/^([A-Za-z_]+)\s*(>=|<=|!=|>|<|=)$/.exec(field);return comparison&&BREEZE_SCHEMA_FIELDS.has(comparison[1])?comparison[1]+':'+({'>=':'gte','<=':'lte','!=':'ne','>':'gt','<':'lt','=':'eq'}[comparison[2]]):'{field}';}));continue; }
    let parsed = value;
    try { parsed = JSON.parse(value); } catch { /* String values stay private. */ }
    let target=values;
    for(const field of fields.slice(0,-1)) {
      if(!target[field] || typeof target[field]!=='object' || Array.isArray(target[field])) target[field]={};
      target=target[field];
    }
    target[fields.at(-1)]=parsed;
  }
  return {...reduceBreezeSchema(values, 0, '', true), unrecognized_parameter_count: Math.min(unrecognized, 10000), unrecognized_parameter_shapes:parameterShapes,filter_field_ids:[...filterFieldIds],filter_operator_ids:[...filterOperatorIds]};
}
function breezeReadRoute(method, value, expectedOrigin) {
  try {
    const url = new URL(value, expectedOrigin);
    if (method === 'POST' && url.origin === expectedOrigin && ["/ajax/get_family_id_by_person_id", "/ajax/get_form_json_by_url_slug", "/ajax/get_forms_list", "/ajax/get_person_from_id", "/ajax/get_profile_fields_json", "/ajax/grouped_payment_details", "/ajax/list_all_people", "/ajax/list_filtered_people", "/ajax/load_archived_forms", "/ajax/load_archived_people", "/ajax/load_form_entries", "/ajax/payment_details_by_payment_id", "/ajax/payments_search_results", "/ajax/people_tag_list", "/ajax/search_followups", "/ajax/show_entry", "/ajax/get_notifications", "/ajax/load_history_table_text", "/ajax/fundraisers_list", "/ajax/pledges_summary", "/ajax/load_event_chart", "/ajax/search_event_attendance"].includes(url.pathname)) {
      return url.pathname;
    }
    if (method !== 'GET' || url.origin !== 'https://api.breezechms.com') return null;
    const parts = url.pathname.replace(/\/{2,}/g, '/').replace(/\/$/, '').split('/');
    return BREEZE_API_READ_PATTERNS.find(pattern => {
      const expected = pattern.split('/');
      return parts.length === expected.length && expected.every((part, index) =>
        /^\{[A-Za-z]+\}$/.test(part) ? parts[index].length > 0 && parts[index].length <= 512 &&
          /^(?:[A-Za-z0-9_-]|%[0-9A-Fa-f]{2})+$/.test(parts[index]) : part === parts[index]);
    }) || null;
  } catch { return null; }
}
function breezeInspectionDocumentAllowed(current, expectedOrigin) {
  try {
    const parts = decodeURIComponent(current.pathname).toLowerCase().split('/').map(p => p.replace(/\.(php|html)$/, ''));
    return current.origin === expectedOrigin && parts.join('/') !== '/api' && parts.filter(Boolean)[0] !== 'settings' &&
      !parts.some(p => ['account', 'account_settings', 'login', 'signin', 'logout', 'oauth', 'api-auth', 'api-key', 'api-keys'].includes(p));
  } catch { return false; }
}
function installBreezeReadSchemas(expectedOrigin) {
  if (!breezeInspectionDocumentAllowed(location, expectedOrigin)) {
    return JSON.stringify({installed: false});
  }
  const key = Symbol.for('breezeInspectionReadSchemas');
  if (globalThis[key]) return JSON.stringify({installed: true});
  let root = globalThis;
  try {
    let parent = globalThis;
    let depth = 0;
    while (parent.parent && parent.parent !== parent) {
      if (++depth > 4 || !breezeInspectionDocumentAllowed(parent.parent.location, expectedOrigin)) {
        return JSON.stringify({installed: false});
      }
      parent = parent.parent;
    }
    root = parent;
  } catch { return JSON.stringify({installed: false}); }
  const registryKey = Symbol.for('breezeInspectionFrameObservers');
  const registry = root[registryKey] || (root[registryKey] = {states: [], truncated: false});
  registry.states = registry.states.filter(state => state.enabled);
  if (registry.states.length >= 32) {
    registry.truncated = true;
    return JSON.stringify({installed: false});
  }
  const state = {samples: [], enabled: true, truncated: false};
  registry.states.push(state);
  let nativeHeaders = null;
  let nativeCredentials = 'omit';
  const centralGet = (method, value) => {
    try {
      const url = new URL(value, expectedOrigin);
      return method === 'GET' && url.origin === 'https://api.breezechms.com' &&
        url.pathname.startsWith('/api/v2/') && !/\/(?:auth|oauth|api-auth|account)(?:\/|$)/.test(url.pathname);
    } catch { return false; }
  };
  state.nativeTemplateReady = () => state.enabled && nativeHeaders !== null;
  state.summarize = () => {
    const active = registry.states.filter(item => item.enabled);
    const samples = active.flatMap(item => item.samples);
    return {observer_installed: state.enabled, samples: samples.slice(-20),
      native_template_ready: state.nativeTemplateReady(),
      frames: active.filter(item => item !== state).map(item => ({same_origin: true,
        observer_installed: true, native_template_ready: item.nativeTemplateReady(), sample_count: item.samples.length})),
      truncated: registry.truncated || active.some(item => item.truncated) || samples.length > 20};
  };
  state.probeContributions = async () => {
    if (!state.nativeTemplateReady()) return JSON.stringify({state:'template_unavailable'});
    const signal=AbortSignal.timeout(18000);const samples=[];const rows=[];
    try {
      for(const page of [1,2]) {
        if(page===2) await new Promise(resolve=>setTimeout(resolve,3500));
        if(!state.enabled) return JSON.stringify({state:'capture_paused',samples});
        const headers=new Headers(nativeHeaders);headers.set('Accept','application/json');
        const response=await fetchOriginal('https://api.breezechms.com/api/v2/contributions?page='+page+'&limit=25',
          {method:'GET',headers,credentials:nativeCredentials,redirect:'error',cache:'no-store',signal});
        if(!response.ok){if(response.body)void response.body.cancel();return JSON.stringify({state:response.status===401?'login_required':response.status===403?'permission_denied':'request_failed',http_status:response.status,samples});}
        const reader=response.body?.getReader();if(!reader)return JSON.stringify({state:'body_unavailable',samples});
        const decoder=new TextDecoder();let text='',bytes=0;
        while(state.enabled){const chunk=await reader.read();if(chunk.done)break;bytes+=chunk.value.length;
          if(bytes>2*1024*1024){void reader.cancel();return JSON.stringify({state:'too_large',samples});}
          text+=decoder.decode(chunk.value,{stream:true});}
        if(!state.enabled){void reader.cancel();return JSON.stringify({state:'capture_paused',samples});}
        const body=JSON.parse(text+decoder.decode());
        samples.push({page,http_status:response.status,schema:redactFinancialMetadata(reduceBreezeSchema(body))});
        const data=Array.isArray(body)?body:[body?.data,body?.results,body?.items].find(Array.isArray);
        if(!data||data.length>25)return JSON.stringify({state:'bound_not_verified',samples});
        rows.push(data);
        if(!data.length)break;
      }
      const ids=rows.map(page=>page.map(row=>row?.id));
      const comparable=ids.length===2&&ids.every(page=>page.length&&page.every(id=>typeof id==='number'||typeof id==='string'));
      return JSON.stringify({state:'completed',samples,counts:rows.map(page=>page.length),
        pages_disjoint:comparable?ids[0].every(id=>!ids[1].includes(id)):null});
    }catch{return JSON.stringify({state:'request_failed',samples});}
  };
  state.probePerson = async () => {
    if (!state.nativeTemplateReady()) return JSON.stringify({state: 'template_unavailable'});
    const signal = AbortSignal.timeout(18000);
    const samples = [];
    const read = async path => {
      if (!state.enabled) throw {kind: 'capture_paused'};
      const headers = new Headers(nativeHeaders);
      headers.set('Accept', 'application/json');
      const response = await fetchOriginal('https://api.breezechms.com/api/v2' + path,
        {method: 'GET', headers, credentials: nativeCredentials, redirect: 'error', cache: 'no-store', signal});
      if (!response.ok) {
        if (response.body) void response.body.cancel();
        throw {kind: response.status === 401 ? 'login_required' : response.status === 403 ? 'permission_denied' : 'request_failed', status: response.status};
      }
      const reader = response.body?.getReader();
      if (!reader) throw {kind: 'body_unavailable'};
      let text = '';
      let bytes = 0;
      const decoder = new TextDecoder();
      while (state.enabled) {
        const chunk = await reader.read();
        if (chunk.done) break;
        bytes += chunk.value.length;
        if (bytes > 2 * 1024 * 1024) { void reader.cancel(); throw {kind: 'too_large'}; }
        text += decoder.decode(chunk.value, {stream: true});
      }
      if (!state.enabled) { void reader.cancel(); throw {kind: 'capture_paused'}; }
      const body = JSON.parse(text + decoder.decode());
      samples.push({stage: samples.length ? 'person' : 'list', http_status: response.status, schema: reduceBreezeSchema(body)});
      return body;
    };
    try {
      const body = await read('/people?limit=1');
      const data = Array.isArray(body) ? body : [body?.data, body?.people, body?.results, body?.items].find(Array.isArray);
      if (!data || data.length > 1) return JSON.stringify({state: 'bound_not_verified', samples});
      if (!data.length) return JSON.stringify({state: 'empty_collection', samples});
      const id = data[0]?.id;
      if (!Number.isSafeInteger(id) || id <= 0) return JSON.stringify({state: 'identifier_contract_changed', samples});
      await new Promise(resolve => setTimeout(resolve, 3500));
      await read('/people/' + id);
      return JSON.stringify({state: 'completed', samples});
    } catch (error) {
      const kinds = ['capture_paused','login_required','permission_denied','request_failed','body_unavailable','too_large'];
      return JSON.stringify({state: kinds.includes(error?.kind) ? error.kind : 'request_failed',
        http_status: Number.isInteger(error?.status) ? error.status : null, samples});
    }
  };
  state.probePeople = async () => {
    if (!state.nativeTemplateReady()) return JSON.stringify({state: 'template_unavailable'});
    const signal = AbortSignal.timeout(18000);
    const samples = [];
    const rows = [];
    const pages = [0, 1, 2];
    try {
      for (let index = 0; index < pages.length; index++) {
        const page = pages[index];
        if (index) await new Promise(resolve => setTimeout(resolve, 3500));
        if (!state.enabled) return JSON.stringify({state: 'capture_paused'});
        const target = new URL('https://api.breezechms.com/api/v2/people');
        target.search = new URLSearchParams({page: String(page), pageSize: '100', sort: 'id'}).toString();
        const headers = new Headers(nativeHeaders);
        headers.set('Accept', 'application/json');
        const response = await fetchOriginal(target.href, {method: 'GET', headers,
          credentials: nativeCredentials, redirect: 'error', cache: 'no-store', signal});
        if (!response.ok) {
          if (response.body) void response.body.cancel();
          return JSON.stringify({state: response.status === 401 ? 'login_required' : response.status === 403 ? 'permission_denied' : 'request_failed',
            http_status: response.status, samples});
        }
        const reader = response.body?.getReader();
        if (!reader) return JSON.stringify({state: 'body_unavailable', samples});
        let text = '';
        let bytes = 0;
        const decoder = new TextDecoder();
        while (state.enabled) {
          const chunk = await reader.read();
          if (chunk.done) break;
          bytes += chunk.value.length;
          if (bytes > 2 * 1024 * 1024) { void reader.cancel(); return JSON.stringify({state: 'too_large', samples}); }
          text += decoder.decode(chunk.value, {stream: true});
        }
        text += decoder.decode();
        const body = JSON.parse(text);
        const data = Array.isArray(body) ? body : [body.data, body.people, body.results, body.items].find(Array.isArray);
        samples.push({page, http_status: response.status, schema: reduceBreezeSchema(body)});
        if (!data || data.length > 100) return JSON.stringify({state: 'paging_not_verified', samples});
        rows.push(data);
        if (index === 0) {
          const last = body?.pagination?.last_page ?? body?.meta?.last_page;
          if (Number.isSafeInteger(last) && last >= 2 && last < 10000) {
            for (const candidate of [last, last + 1]) if (!pages.includes(candidate)) pages.push(candidate);
          }
        }
      }
      const ids = rows.map(page => page.map(row => row?.id));
      const comparable = page => page.length > 0 && page.every(id => typeof id === 'string' || typeof id === 'number');
      return JSON.stringify({state: 'completed', samples, pages, counts: rows.map(page => page.length),
        page_zero_matches_one: comparable(ids[0]) && comparable(ids[1]) ? JSON.stringify(ids[0]) === JSON.stringify(ids[1]) : null,
        pages_one_two_disjoint: comparable(ids[1]) && comparable(ids[2]) ? ids[1].every(id => !ids[2].includes(id)) : null});
    } catch { return JSON.stringify({state: 'request_failed', samples}); }
  };
  const save = (method, route, status, body) => {
    if (!state.enabled || !breezeInspectionDocumentAllowed(location, expectedOrigin)) return;
    if (route.startsWith('/api/v2/contributions') && body.schema) redactFinancialMetadata(body.schema);
    state.samples.push({method, route, status, ...body});
    if (state.samples.length > 20) {state.samples.shift();state.truncated=true;}
  };
  const fetchOriginal = globalThis.fetch;
  const fetchWrapped = async function(input, init) {
    if (!state.enabled || !breezeInspectionDocumentAllowed(location, expectedOrigin)) {
      return Reflect.apply(fetchOriginal, this, [input, init]);
    }
    const response = await Reflect.apply(fetchOriginal, this, [input, init]);
    const method = (init?.method || (input instanceof Request ? input.method : 'GET')).toUpperCase();
    const route = breezeReadRoute(method, input instanceof Request ? input.url : String(input), expectedOrigin);
    const requestSchema = route && method === 'GET' ? reduceBreezeRequest(new URL(input instanceof Request ? input.url : String(input), expectedOrigin).searchParams) : null;
    if (state.enabled && response.ok && centralGet(method, input instanceof Request ? input.url : String(input))) {
      try {
        const request = new Request(input, init);
        if (request.headers.has('Authorization')) {
          nativeHeaders = new Headers(request.headers);
          nativeCredentials = request.credentials;
        }
      } catch { /* Preserve the website request even if no template can be retained. */ }
    }
    if (route && state.enabled) {
      if (!response.ok) save(method, route, response.status, {format: 'http_error', request_schema: requestSchema});
      else {
        const clone = response.clone();
        (async () => {
          try {
            const reader = clone.body?.getReader();
            if (!reader) return;
            const decoder = new TextDecoder();
            let size = 0;
            let text = '';
            while (state.enabled) {
              const chunk = await reader.read();
              if (chunk.done) break;
              size += chunk.value.length;
              if (size > 2 * 1024 * 1024) {
                void reader.cancel();
                save(method, route, response.status, {format: 'too_large'});
                return;
              }
              text += decoder.decode(chunk.value, {stream: true});
            }
            text += decoder.decode();
            save(method, route, response.status, {...reduceBreezeBody(text), request_schema: requestSchema});
          } catch { save(method, route, response.status, {format: 'unavailable'}); }
        })();
      }
    }
    return response;
  };
  globalThis.fetch = fetchWrapped;
  const xhrOpen = XMLHttpRequest.prototype.open;
  const xhrSend = XMLHttpRequest.prototype.send;
  const xhrHeader = XMLHttpRequest.prototype.setRequestHeader;
  const requests = new WeakMap();
  const openWrapped = function(method, url, ...rest) {
    if (!state.enabled || !breezeInspectionDocumentAllowed(location, expectedOrigin)) {
      return Reflect.apply(xhrOpen, this, [method, url, ...rest]);
    }
    const verb = String(method).toUpperCase();
    requests.set(this, {method: verb, route: breezeReadRoute(verb, String(url), expectedOrigin),
      query: verb === 'GET' ? new URL(String(url), expectedOrigin).searchParams : null,
      central: centralGet(verb, String(url)), headers: new Headers()});
    return Reflect.apply(xhrOpen, this, [method, url, ...rest]);
  };
  const headerWrapped = function(name, value) {
    const result = Reflect.apply(xhrHeader, this, [name, value]);
    const request = requests.get(this);
    if (request?.central && String(name).toLowerCase() === 'authorization') {
      try { request.headers.set(name, value); } catch { /* Keep native behavior. */ }
    }
    return result;
  };
  const sendWrapped = function(...args) {
    const request = requests.get(this);
    const requestSchema = request?.route ? reduceBreezeRequest(request.query || args[0]) : null;
    if (request?.route || request?.central) this.addEventListener('load', () => {
      if (!state.enabled) return;
      if (request.central && this.status >= 200 && this.status < 300 && request.headers.has('Authorization')) {
        nativeHeaders = new Headers(request.headers);
        nativeCredentials = this.withCredentials ? 'include' : 'omit';
      }
      if (!request.route) return;
      try {
        const body = this.status < 200 || this.status >= 300 ? {format: 'http_error'} :
          this.responseType === 'json' ? {format: 'json', schema: reduceBreezeSchema(this.response)} :
          ['', 'text'].includes(this.responseType) ? reduceBreezeBody(this.responseText) : {format: 'unavailable'};
        save(request.method, request.route, this.status, {...body, request_schema: requestSchema});
      } catch { save(request.method, request.route, this.status, {format: 'unavailable'}); }
    }, {once: true});
    return Reflect.apply(xhrSend, this, args);
  };
  XMLHttpRequest.prototype.open = openWrapped;
  XMLHttpRequest.prototype.send = sendWrapped;
  XMLHttpRequest.prototype.setRequestHeader = headerWrapped;
  state.stop = () => {
    if (root === globalThis) {
      for (const child of [...registry.states]) if (child !== state && child.enabled) child.stop();
    }
    state.enabled = false;
    nativeHeaders = null;
    if (globalThis.fetch === fetchWrapped) globalThis.fetch = fetchOriginal;
    if (XMLHttpRequest.prototype.open === openWrapped) XMLHttpRequest.prototype.open = xhrOpen;
    if (XMLHttpRequest.prototype.send === sendWrapped) XMLHttpRequest.prototype.send = xhrSend;
    if (XMLHttpRequest.prototype.setRequestHeader === headerWrapped) XMLHttpRequest.prototype.setRequestHeader = xhrHeader;
    delete globalThis[key];
    registry.states = registry.states.filter(item => item !== state && item.enabled);
  };
  globalThis[key] = state;
  globalThis.addEventListener?.('pagehide', state.stop, {once: true});
  return JSON.stringify({installed: true});
}
