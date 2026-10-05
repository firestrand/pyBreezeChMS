/* Fixed SDK double; import is replaced in this test only, never in live code. */
(async () => {
  // READ_SCANNER
  // V2_SCANNER
  const moduleUrl = 'https://main.ddgv4rlrmu56c.amplifyapp.com/assets/main-BkBiSYb4.js';
  const document = {querySelectorAll: () => [{src: moduleUrl}]};
  const performance = {getEntriesByType: () => []};
  let calls = 0;
  let deny = false;
  const loadSyntheticFrontend = async url => {
    if (url !== moduleUrl) throw Error('Unexpected module');
    return {a: base => {
      if (base !== 'https://api.breezechms.com/api/v2') throw Error('Unexpected base');
      return {people: {getPeople: async options => {
        if (options.pageSize !== 2 || options.sort !== 'id' || options.noLimit !== false) throw Error('Unbounded request');
        calls++;
        if (deny) throw {status: 403, body: 'PRIVATE_ERROR'};
        const start = options.page <= 1 ? 1 : 3;
        return {data: [{id: start, name: 'PRIVATE_PERSON'}, {id: start + 1, name: 'PRIVATE_PERSON'}], meta: {page: options.page}};
      }}};
    }};
  };
  const result = JSON.parse(await probeBreezeV2People());
  deny = true;
  const failed = JSON.parse(await probeBreezeV2People());
  const checks = {
    fixed_page_size: JSON.stringify(result.counts) === '[2,2,2]',
    base_detectable_without_ids: result.page_zero_matches_one === true && result.pages_one_two_disjoint === true,
    no_records_or_error_bodies: !JSON.stringify([result,failed]).includes('PRIVATE_'),
    permission_failure_stops: failed.state === 'permission_denied' && calls === 4
  };
  return JSON.stringify({checks, passed: Object.values(checks).every(Boolean)});
})()
