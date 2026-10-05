/* Fixed synthetic privacy checks; no real page, network or record access. */
(() => {
  const sample = `
    const secret = 'SYNTHETIC_PRIVATE_TOKEN';
    const record = {name:'SYNTHETIC_PRIVATE_PERSON'};
    const fake = "$.ajax({type:'POST',url:'/ajax/delete_people',data:{private_name:'secret'}})";
    // $.ajax({type:'POST',url:'/ajax/save_record',data:{private_value:'secret'}})
    $.ajax({type:'POST',url:'../../ajax/get_forms_list',data:{limit:2,sort:'name',secret:secret},success:function(data){render(data);}});
    $.ajax({url:'/ajax/get_people',method:'GET',data:query,success:render});
    $.ajax({url:dynamic,method:'GET',data:{token:secret}});
  `;
  const location={origin:'https://demo.breezechms.com'};
  const globalThis={performance:{getEntriesByType:()=>[{name:'https://api.breezechms.com/api/v2//contributions?page=1&filter=SYNTHETIC_PRIVATE_TOKEN&private_name=secret',initiatorType:'fetch'}]}};
  const document = {querySelectorAll: selector => selector==='a[href]' ? [{href:location.origin+'/people/edit/123?private_name=SYNTHETIC_PRIVATE_TOKEN'}] : [{textContent: sample}]};
  // PAGE_SCANNER
  const result = JSON.parse(inspectPageContracts());
  const encoded = JSON.stringify(result);
  const checks = {
    request_diagnostics_hide_url_values: result.contribution_requests[0].empty_path_segments===1&&JSON.stringify(result.contribution_requests[0].query_keys)===JSON.stringify(['filter','page','{field}']),
    view_diagnostics_hide_ids_and_labels: result.view_actions[0].tokens[0]==='edit'&&!encoded.includes('123'),
    only_real_declarations: result.declarations.length === 2,
    relative_url_normalized: result.declarations[0].route === '/ajax/get_forms_list',
    request_keys_only: JSON.stringify(result.declarations[0].request_keys) === JSON.stringify(['limit','secret','sort']),
    no_values: !encoded.includes('SYNTHETIC_PRIVATE'),
    computed_data_marked: result.declarations[1].computed_data === true,
    computed_url_ignored: result.declarations.every(d => d.route !== 'dynamic')
  };
  return JSON.stringify({checks, passed: Object.values(checks).every(Boolean)});
})()
