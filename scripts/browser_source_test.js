/* Fixed synthetic browser test. No network or real DOM/storage access. */
(async () => {
  const globalThis = {};
  const location = {origin: 'https://demo.breezechms.com'};
  const scriptUrls = [
    {src: 'https://demo.breezechms.com/js/test.js'},
    {src: 'https://demo.breezechms.com/api/people'},
    {src: 'https://unapproved.example/assets/evil.js'}
  ];
  const document = {querySelectorAll: () => scriptUrls};
  const performance = {getEntriesByType: () => [{name: 'https://app.breezechms.com/js/resource_only'}]};
  const secret = 'SYNTHETIC_PRIVATE_TOKEN_VALUE';
  const sample = 'class Client {static list(t={}) {return request({method:"GET",url:"/people",query:{page:t.page,pageSize:t.pageSize}})}static create(t){return request({method:"POST",url:"/people",body:t})}}; api.get("contributions?filter[paid_on >]=secret-query");api.get("/people",{params:{api:JSON.stringify({page:1,filter:privateValue})}}); const token="' + secret + '"; const privateRoute="/people/PrivatePerson/123?id=secret-query"; const relative="../../ajax/read_people"; api.post("/auth/access_token",{grant_type:"session_token",session_token:token});';
  let fetches = 0;
  const fetch = async (url, options) => {
    if (!['https://demo.breezechms.com/js/test.js', 'https://app.breezechms.com/js/test_source', 'https://app.breezechms.com/js/html_source', 'https://shared.breezechms.com/js/shared.js'].includes(url) || options.credentials !== 'omit' || options.method !== 'GET') throw Error('Synthetic fetch boundary failed');
    fetches++;
    return new Response(sample + (url.endsWith('/shared.js') ? ' api.get("contributions/overview",{params:{config:config}});' : ''), {headers: {'content-type': url.endsWith('html_source') ? 'text/html' : 'application/javascript'}});
  };
  // SOURCE_SCANNER
  const assets = JSON.parse(await inspectBrowserSource('assets', null));
  const result = JSON.parse(await inspectBrowserSource('source', 0));
  const encoded = JSON.stringify(result);
  const list = result.declarations.find(d => d.method === 'GET' && d.route === '/people');
  scriptUrls.push({src: 'https://demo.breezechms.com/js/aaa.js'});
  scriptUrls.push({src: 'https://app.breezechms.com/js/test_source'});
  scriptUrls.push({src: 'https://app.breezechms.com/js/html_source'});
  const expanded = JSON.parse(await inspectBrowserSource('assets', null));
  const cache = globalThis[Symbol.for('breezeInspectionAssets')];
  const shared = JSON.parse(await inspectBrowserSource('source', cache.indexOf('https://app.breezechms.com/js/test_source')));
  const html = JSON.parse(await inspectBrowserSource('source', cache.indexOf('https://app.breezechms.com/js/html_source')));
  scriptUrls.push({src:'https://shared.breezechms.com/js/shared.js'});
  scriptUrls.push({src:'https://shared.breezechms.com/js/secret.js?token=SYNTHETIC_SECRET_QUERY'});
  const sharedInventory=JSON.parse(await inspectBrowserSource('assets',null));
  const sharedSource=JSON.parse(await inspectBrowserSource('source',cache.indexOf('https://shared.breezechms.com/js/shared.js')));
  globalThis[Symbol.for('breezeInspectionAssets')][0] = 'https://demo.breezechms.com/api/people';
  const tampered = JSON.parse(await inspectBrowserSource('source', 0));
  const checks = {
    observed_breeze_origin_static_read: sharedSource.declarations.some(d=>d.route==='contributions/overview'&&d.method==='GET'),
    credential_query_asset_never_fetched: !cache.some(url=>url.includes('SYNTHETIC_SECRET_QUERY'))&&sharedInventory.breeze_script_locations.every(item=>!JSON.stringify(item).includes('SYNTHETIC_SECRET_QUERY')),
    only_static_assets: assets.count === 1,
    relative_query_contract_is_metadata_only: result.references.some(r=>r.route==='contributions'&&r.literal_query_keys[0]==='filter[paid_on >]')&&!encoded.includes('secret-query'),
    wrapper_metadata_has_no_source_or_values: result.request_wrapper_shapes[0]?.api_value_form==='json_stringify'&&!JSON.stringify(result.request_wrapper_shapes).includes(secret),
    no_secret_values: !encoded.includes(secret) && !encoded.includes('secret-query') && !encoded.includes('PrivatePerson'),
    exact_method_not_neighbor: list?.method === 'GET' && list?.sdk_method === 'list',
    query_names_only: JSON.stringify(list?.query_keys) === JSON.stringify(['page', 'pageSize']),
    dynamic_ids_hidden: result.references.some(r => r.route === '/people/{segment}/{segment}'),
    no_account_network: fetches === 4,
    no_source_snippets: !Object.hasOwn(result, 'contexts'),
    asset_indices_stable: expanded.assets[0].filename === 'test.js',
    cached_urls_revalidated: tampered.error === 'asset_location_refused' && fetches === 4,
    shared_static_source_allowed: shared.sha256 === result.sha256,
    extensionless_requires_script_initiator: !cache.includes('https://app.breezechms.com/js/resource_only'),
    extensionless_html_refused: html.error === 'asset_type_refused',
    relative_ajax_normalized: result.references.some(r => r.route === '/ajax/read_people')
  };
  return JSON.stringify({checks, passed: Object.values(checks).every(Boolean)});
})()
