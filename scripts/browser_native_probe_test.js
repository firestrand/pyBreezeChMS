/* Fake browser primitives verify opaque credentials never enter summaries. */
(async () => {
  const privateToken = 'SYNTHETIC_PRIVATE_BEARER';
  const location = {origin: 'https://demo.breezechms.com', pathname: '/people'};
  const setTimeout = callback => {callback(); return 0;};
  let calls = 0;
  let deny = false;
  let emptyThird = false;
  let declaredLast = null;
  let oversized = false;
  let personMode = null;
  let personCalls = 0;
  const globalThis = {fetch: async (input, init) => {
    const request = new Request(input, init);
    if (request.headers.get('Authorization') !== privateToken) throw Error('Native headers not preserved');
    if (!request.url.startsWith('https://api.breezechms.com/api/v2/')) throw Error('Wrong origin');
    calls++;
    if (deny) return new Response('SYNTHETIC_PRIVATE_ERROR', {status: 403});
    const url = new URL(request.url);
    if (url.pathname.endsWith('/integrations')) return new Response('{}');
    if(url.pathname==='/api/v2/contributions') {
      if(url.searchParams.get('limit')!=='25'||!['1','2'].includes(url.searchParams.get('page')))throw Error('Wrong contribution read');
      return new Response(JSON.stringify({data:Array.from({length:oversized?26:2},(_,i)=>({id:'SYNTHETIC_PRIVATE_ID_'+url.searchParams.get('page')+'_'+i,amount:7319})),meta:{total:7319}}));
    }
    if (personMode) {
      personCalls++;
      if (url.pathname === '/api/v2/people' && url.searchParams.get('limit') === '1') {
        const data = [{id: personMode === 'invalid' ? '../account' : 123}];
        if (personMode === 'unbounded') data.push({id: 124});
        return new Response(JSON.stringify({data}));
      }
      if (url.pathname !== '/api/v2/people/123') throw Error('Unexpected detail path');
      if (personMode === 'denied') return new Response('SYNTHETIC_PRIVATE_ERROR', {status: 403});
      return new Response(JSON.stringify({data: {id: 123, first_name: 'SYNTHETIC_PRIVATE_PERSON', fields: {SYNTHETIC_PRIVATE_KEY: 'SYNTHETIC_PRIVATE_VALUE'}}}));
    }
    if (url.pathname !== '/api/v2/people' || url.searchParams.get('pageSize') !== '100' ||
        url.searchParams.has('per_page') || url.searchParams.has('limit')) throw Error('Wrong read');
    if (oversized) return new Response(JSON.stringify({data: Array.from({length: 101}, (_, id) => ({id}))}));
    if (declaredLast !== null && Number(url.searchParams.get('page')) > declaredLast) return new Response('{"data":[]}');
    if (emptyThird && url.searchParams.get('page') === '2') return new Response('{"data":[]}');
    const start = Number(url.searchParams.get('page')) <= 1 ? 1 : 3;
    return new Response(JSON.stringify({data: [
      {id: 'SYNTHETIC_PRIVATE_ID_' + start, name: 'SYNTHETIC_PRIVATE_PERSON'},
      {id: 'SYNTHETIC_PRIVATE_ID_' + (start + 1), name: 'SYNTHETIC_PRIVATE_PERSON'}
    ], ...(declaredLast !== null ? {pagination: {last_page: declaredLast}} : {})}));
  }};
  class XMLHttpRequest {
    open() {}
    send() {for (const callback of this.listeners || []) callback();}
    setRequestHeader() {}
    addEventListener(_event, callback) {(this.listeners ||= []).push(callback);}
    status = 200;
    withCredentials = false;
  }
  // READ_SCANNER
  installBreezeReadSchemas(location.origin);
  const state = globalThis[Symbol.for('breezeInspectionReadSchemas')];
  const empty = JSON.parse(await state.probePeople());
  await globalThis.fetch('https://api.breezechms.com/api/v2/integrations', {headers: {Authorization: privateToken}});
  const ready = state.nativeTemplateReady();
  const result = JSON.parse(await state.probePeople());
  emptyThird = true;
  const terminal = JSON.parse(await state.probePeople());
  deny = true;
  const failed = JSON.parse(await state.probePeople());
  const baseCalls = calls;
  deny = false;
  emptyThird = false;
  declaredLast = 3;
  const ending = JSON.parse(await state.probePeople());
  const endingCalls = calls - baseCalls;
  oversized = true;
  const beforeOversized = calls;
  const stopped = JSON.parse(await state.probePeople());
  const oversizedCalls = calls - beforeOversized;
  personMode = 'ok';
  const detail = JSON.parse(await state.probePerson());
  personMode = 'invalid';
  const invalid = JSON.parse(await state.probePerson());
  personMode = 'unbounded';
  const unbounded = JSON.parse(await state.probePerson());
  personMode = 'denied';
  const denied = JSON.parse(await state.probePerson());
  personMode = null;
  oversized=false;const contributions=JSON.parse(await state.probeContributions());
  oversized=true;const contributionBase=calls;const contributionBound=JSON.parse(await state.probeContributions());const contributionBoundCalls=calls-contributionBase;
  deny=true;const contributionDenied=JSON.parse(await state.probeContributions());deny=false;
  state.stop();
  const cleared = !state.nativeTemplateReady();
  installBreezeReadSchemas(location.origin);
  const xhrState = globalThis[Symbol.for('breezeInspectionReadSchemas')];
  const xhr = new XMLHttpRequest();
  xhr.open('GET','https://api.breezechms.com/api/v2/integrations');
  xhr.setRequestHeader('Authorization', privateToken);
  xhr.send();
  const xhrReady = xhrState.nativeTemplateReady();
  for(let i=0;i<24;i++){const extra=new XMLHttpRequest();extra.open('GET','https://api.breezechms.com/api/v2/integrations');extra.send();}
  const ownCap=xhrState.summarize();
  let childStopped = false;
  const child = {enabled: true, samples: Array.from({length:21}, () => ({path:'/ajax/get_forms_list',http_status:200})),
    nativeTemplateReady: () => false, stop: () => {child.enabled=false;childStopped=true;}};
  globalThis[Symbol.for('breezeInspectionFrameObservers')].states.push(child);
  const frameSummary = xhrState.summarize();
  xhrState.stop();
  const checks = {
    per_document_summary_cap_is_explicit: ownCap.samples.length===20&&ownCap.truncated,
    contributions_two_bounded_disjoint_pages: contributions.state==='completed'&&JSON.stringify(contributions.counts)==='[2,2]'&&contributions.pages_disjoint,
    contributions_values_and_financial_metadata_private: !JSON.stringify([contributions,contributionBound,contributionDenied]).includes('SYNTHETIC_PRIVATE')&&!JSON.stringify(contributions).includes('7319'),
    contributions_unbounded_stops: contributionBound.state==='bound_not_verified'&&contributionBoundCalls===1,
    contributions_permission_failure: contributionDenied.state==='permission_denied',
    no_replay_without_template: empty.state === 'template_unavailable',
    successful_fetch_template_only: ready,
    successful_xhr_template_only: xhrReady,
    frame_summaries_bounded_and_truncation_explicit: frameSummary.frames.length === 1 && frameSummary.samples.length === 20 && frameSummary.truncated,
    pause_stops_child_observers: childStopped && !child.enabled && globalThis[Symbol.for('breezeInspectionFrameObservers')].states.length === 0,
    bounded_pages: JSON.stringify(result.counts) === '[2,2,2]' && baseCalls === 8,
    declared_end_checked_with_five_reads: JSON.stringify(ending.pages) === '[0,1,2,3,4]' && ending.counts[4] === 0 && endingCalls === 5,
    oversized_page_stops_after_one_read: stopped.state === 'paging_not_verified' && oversizedCalls === 1,
    detail_read_is_bounded_and_private: detail.state === 'completed' && detail.samples[1].schema.fields.data.fields.first_name.type === 'string' && !JSON.stringify([detail,invalid,unbounded,denied]).includes('SYNTHETIC_PRIVATE') && !JSON.stringify(detail).includes('123'),
    detail_invalid_or_unbounded_stops: invalid.state === 'identifier_contract_changed' && unbounded.state === 'bound_not_verified' && personCalls === 6,
    detail_permission_failure: denied.state === 'permission_denied',
    ids_compared_without_export: result.page_zero_matches_one && result.pages_one_two_disjoint,
    permission_failure_stops: failed.state === 'permission_denied',
    empty_page_preserves_base_comparison: terminal.page_zero_matches_one === true && terminal.pages_one_two_disjoint === null && terminal.counts[2] === 0,
    credentials_and_records_private: !JSON.stringify([result,failed,state.samples]).includes('SYNTHETIC_PRIVATE'),
    pause_clears_credentials: cleared
  };
  return JSON.stringify({checks, passed: Object.values(checks).every(Boolean)});
})()
