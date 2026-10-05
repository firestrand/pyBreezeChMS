/* Synthetic schema privacy checks. Does not install hooks or issue requests. */
(() => {
  // READ_SCANNER
  const privateValue = 'SYNTHETIC_PRIVATE_PERSON_AND_TOKEN';
  const json = reduceBreezeBody(JSON.stringify({data: [{id: 123, name: privateValue,
    private_field_name: privateValue, fields: {private_field_name: privateValue}}],
    meta: {page: 1, total: 50}, access_token: privateValue}));
  const html = reduceBreezeBody('<table><tr><td>' + privateValue + '</td></tr></table>');
  const encoded = JSON.stringify([json, html]);
  const request = reduceBreezeRequest('options[page]=0&options[limit]=50&options[search]=SYNTHETIC_PRIVATE_PERSON_AND_TOKEN&secret=SYNTHETIC_PRIVATE_PERSON_AND_TOKEN');
  const origin = 'https://demo.breezechms.com';
  const query = reduceBreezeRequest(new URL('https://api.breezechms.com/api/v2/tags?page=1&pageSize=2&filter=%7B%22name%22%3A%22SYNTHETIC_PRIVATE_PERSON_AND_TOKEN%22%7D').searchParams);
  const privateCount = reduceBreezeSchema({data: {count: 7319}, meta: {total: 50}});
  const globalThis = {};
  let location = {origin, pathname: '/%61ccount.php/api'};
  const excludedInstall = JSON.parse(installBreezeReadSchemas(origin));
  location = {origin, pathname: '/people'};
  globalThis.parent = {location: {origin, pathname: '/account'}};
  const excludedParent = JSON.parse(installBreezeReadSchemas(origin));
  delete globalThis.parent;
  globalThis[Symbol.for('breezeInspectionFrameObservers')] = {states: Array.from({length:32}, () => ({enabled:true})), truncated:false};
  const cappedInstall = JSON.parse(installBreezeReadSchemas(origin));
  const financial = redactFinancialMetadata(reduceBreezeSchema({meta:{total:7319,count:42},data:[{amount:7319}]}));
  const config = reduceBreezeRequest('config=%7B%22page%22%3A1%2C%22limit%22%3A50%2C%22filter%22%3A%7B%22total%22%3A7319%7D%7D');
  const apiRequest=reduceBreezeRequest('api[pagination][page]=1&api[pagination][limit]=50&api[filter][total]=7319&api[filter][fund_id]=7319&api[__proto__][name]=SYNTHETIC_PRIVATE_PERSON_AND_TOKEN');
  const filterRequest=reduceBreezeRequest('filter[paid_on][gte]=SYNTHETIC_PRIVATE_PERSON_AND_TOKEN&filter[paid_on][lte]=SYNTHETIC_PRIVATE_PERSON_AND_TOKEN');
  const compared=reduceBreezeRequest('filter[paid_on%3E%3D]=SYNTHETIC_PRIVATE_PERSON_AND_TOKEN&filter[private_name%3C]=secret');
  const hyphenFilter=reduceBreezeRequest('filter[paid_on-gte]=SYNTHETIC_PRIVATE_PERSON_AND_TOKEN&filter[paid_on-lte]=SYNTHETIC_PRIVATE_PERSON_AND_TOKEN');
  const indexed=reduceBreezeRequest('filter[0]='+encodeURIComponent(JSON.stringify(['paid_on','gte',privateValue]))+'&filter[1]='+encodeURIComponent(JSON.stringify({field:privateValue,operator:privateValue,value:7319})));
  const checks = {
    indexed_filters_type_only_and_selectors_curated: indexed.unrecognized_parameter_count===0&&indexed.fields.filter.type==='array'&&JSON.stringify(indexed.filter_field_ids)==='["paid_on"]'&&JSON.stringify(indexed.filter_operator_ids)==='["gte"]'&&!JSON.stringify(indexed).includes(privateValue)&&!JSON.stringify(indexed).includes('7319'),
    hyphen_filter_operators_typed_and_private: hyphenFilter.unrecognized_parameter_count===0&&hyphenFilter.fields.filter.fields.paid_on.fields.gte.type==='string'&&!JSON.stringify(hyphenFilter).includes(privateValue),
    comparison_key_shapes_keep_only_curated_fields: JSON.stringify(compared.unrecognized_parameter_shapes)===JSON.stringify([['filter','paid_on:gte'],['filter','{field}']])&&!JSON.stringify(compared).includes(privateValue),
    bracket_date_filters_typed_and_private: filterRequest.unrecognized_parameter_count===0&&filterRequest.fields.filter.fields.paid_on.fields.gte.type==='string'&&!JSON.stringify(filterRequest).includes(privateValue),
    no_private_values: !encoded.includes(privateValue) && !encoded.includes('123'),
    unknown_keys_hidden: !encoded.includes('private_field_name') && !encoded.includes('access_token'),
    approved_fields_and_types: json.schema.fields.data.samples[0].fields.name.type === 'string',
    array_count_only: json.schema.fields.data.count === 1,
    record_counts_are_private_outside_metadata: privateCount.fields.data.fields.count.type === 'number' && !('value' in privateCount.fields.data.fields.count) && privateCount.fields.meta.fields.total.value === 50,
    excluded_document_never_installs: excludedInstall.installed === false && !globalThis.fetch,
    excluded_parent_never_installs: excludedParent.installed === false,
    frame_installation_cap_explicit: cappedInstall.installed === false && globalThis[Symbol.for('breezeInspectionFrameObservers')].truncated,
    financial_metadata_never_returns_numbers: !JSON.stringify(financial).includes('7319') && !JSON.stringify(financial).includes('42') && financial.fields.meta.fields.total.type === 'number',
    config_paging_preserved_filters_private: config.fields.config.fields.limit.value === 50 && !('value' in config.fields.config.fields.filter.fields.total),
    nested_api_request_paging_only: apiRequest.fields.api.fields.pagination.fields.page.value === 1 && apiRequest.fields.api.fields.pagination.fields.limit.value === 50 && !JSON.stringify(apiRequest).includes('7319') && !JSON.stringify(apiRequest).includes(privateValue) && apiRequest.unrecognized_parameter_count === 1,
    html_counts_only: html.format === 'html' && html.tag_counts.tr === 1,
    oversized_body_rejected: reduceBreezeBody('x'.repeat(2 * 1024 * 1024 + 1)).format === 'too_large',
    reviewed_collection_trailing_slash: breezeReadRoute('GET','https://api.breezechms.com/api/v2/contributions/',origin)==='/api/v2/contributions',
    repeated_separator_read_contract: breezeReadRoute('GET','https://api.breezechms.com/api/v2//contributions/',origin)==='/api/v2/contributions',
    auth_routes_excluded: breezeReadRoute('GET','https://api.breezechms.com/api/v2/auth/sessionkey',origin) === null,
    private_path_values_become_templates: breezeReadRoute('GET','https://api.breezechms.com/api/v2/people/123/notes/456',origin) === '/api/v2/people/{person}/notes/{note}',
    unknown_or_transition_routes_excluded: breezeReadRoute('GET','https://api.breezechms.com/api/v2/not-reviewed',origin) === null && breezeReadRoute('GET','https://api.breezechms.com/api/v2/users/impersonate/123',origin) === null,
    writes_excluded: breezeReadRoute('POST',origin + '/ajax/form_create_content',origin) === null,
    giving_read_reviewed_and_refund_excluded: breezeReadRoute('POST',origin + '/ajax/payments_search_results',origin) === '/ajax/payments_search_results' && breezeReadRoute('POST',origin + '/ajax/refund_charge',origin) === null,
    cross_origin_excluded: breezeReadRoute('POST','https://evil.example/ajax/get_forms_list',origin) === null,
    request_pagination_only: request.fields.options.fields.page.value === 0 && request.fields.options.fields.limit.value === 50,
    request_values_hidden: !JSON.stringify(request).includes(privateValue) && !JSON.stringify(request).includes('secret'),
    get_query_pagination_and_filter_private: query.fields.pageSize.value === 2 && query.fields.filter.fields.name.type === 'string' && !JSON.stringify(query).includes(privateValue)
  };
  return JSON.stringify({checks, passed: Object.values(checks).every(Boolean)});
})()
