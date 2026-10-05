/* Fixed synthetic probe; fake jQuery performs no network access. */
(async () => {
  // READ_SCANNER
  // PROBE_SCANNER
  let calls = 0;
  const jQuery = {ajax: options => {
    if (options.type !== 'POST' || options.url !== '/ajax/list_all_people' ||
        ![2,3].includes(options.data.limit) || options.headers) throw Error('Probe boundary failed');
    calls++;
    const rows = Array.from({length: options.data.limit}, (_, i) => ({id: 'PRIVATE_ID_' + i, name: 'PRIVATE_NAME'}));
    options.success(JSON.stringify(rows), 'success', {status: 200});
  }};
  const result = JSON.parse(await probeBreezePeople());
  const checks = {
    only_two_bounded_reads: calls === 2,
    counts_verified: JSON.stringify(result.array_counts) === '[2,3]' && result.limit_honored === true,
    order_comparison_without_ids: result.prefix_stable === true && !JSON.stringify(result).includes('PRIVATE_')
  };
  return JSON.stringify({checks, passed: Object.values(checks).every(Boolean)});
})()
