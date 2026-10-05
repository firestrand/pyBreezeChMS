/* Synthetic document reads; fake DOM/fetch only, no account navigation. */
(async () => {
  // READ_SCANNER
  // DOCUMENT_SCANNER
  const origin='https://demo.breezechms.com';let mode='html';let calls=0;let canceled=0;
  const html='<p>SYNTHETIC_PRIVATE_PERSON</p><script>const record="SYNTHETIC_PRIVATE_TOKEN";$.ajax({type:"POST",url:"/ajax/get_forms_list",data:{limit:2}});</script><a href="/people/view/123">Private label</a><a href="/forms?token=private">Hidden</a><a download href="/file.csv">Download</a>';
  const globalThis={document:{createElement:()=>({set innerHTML(value){this.value=value;},content:{querySelector:()=>null}})}};
  globalThis.document.createElement=()=>{
    let attributes='';return {set innerHTML(value){attributes=value;},content:{querySelector:()=>{
      const href=/href="([^"]+)"/.exec(attributes)?.[1];return href?{hasAttribute:name=>name==='download'&&/\bdownload\b/.test(attributes),getAttribute:()=>href}:null;
    }}};
  };
  globalThis[Symbol.for('breezeInspectionReadSchemas')]={enabled:true};
  const fetch=async(_url,options)=>{
    if(options.method!=='GET'||options.credentials!=='same-origin'||options.redirect!=='manual') throw Error('Wrong request');calls++;
    if(mode==='redirect') return {type:'opaqueredirect',body:null};
    if(mode==='login') return {type:'basic',ok:false,status:401,body:{cancel:async()=>canceled++}};
    if(mode==='attachment') return new Response(html,{headers:{'Content-Type':'text/html','Content-Disposition':'attachment; filename=PRIVATE_NAME'}});
    return new Response(mode==='large'?'x'.repeat(2*1024*1024+1):html,{headers:{'Content-Type':'text/html'}});
  };
  const read=()=>inspectReadonlyBrowserDocument(origin+'/events/people/123/out',origin).then(JSON.parse);
  const normal=await read();mode='attachment';const attachment=await read();mode='login';const login=await read();mode='large';const large=await read();mode='redirect';const redirect=await read();
  const excluded=JSON.parse(await inspectReadonlyBrowserDocument(origin+'/%61ccount/api',origin));
  const cross=JSON.parse(await inspectReadonlyBrowserDocument('https://other.breezechms.com/events/123',origin));
  globalThis[Symbol.for('breezeInspectionReadSchemas')].enabled=false;const paused=await read();
  const checks={
    html_contracts_reduced:normal.state==='html_inspected'&&normal.declarations.length===1&&normal.declarations[0].route==='/ajax/get_forms_list',
    records_scripts_and_filenames_not_returned:!JSON.stringify([normal,attachment,login,large,redirect]).includes('SYNTHETIC_PRIVATE')&&!JSON.stringify(attachment).includes('PRIVATE_NAME'),
    credential_and_download_links_rejected:normal.links.length===1&&normal.links[0]===origin+'/people/view/123',
    attachments_not_read:attachment.state==='non_html_or_attachment',
    login_body_canceled:login.state==='login_required'&&canceled===1,
    byte_bound_stops:large.state==='too_large',
    redirects_not_followed:redirect.state==='redirect_unresolved',
    excluded_and_cross_origin_never_requested:excluded.state==='target_rejected'&&cross.state==='target_rejected'&&calls===5,
    capture_pause_stops:paused.state==='capture_paused'&&calls===5
  };
  return JSON.stringify({checks,passed:Object.values(checks).every(Boolean)});
})()
