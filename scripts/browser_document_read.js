/* Read an approved document as inert text; never execute or return page content. */
async function inspectReadonlyBrowserDocument(target, expectedOrigin) {
  const url = new URL(target);
  if (url.origin !== expectedOrigin || !breezeInspectionDocumentAllowed(url, expectedOrigin) ||
      url.username || url.password || Array.from(url.searchParams.keys()).some(k => /token|secret|password|session|auth|^key$/i.test(k))) {
    return JSON.stringify({state:'target_rejected',links:[]});
  }
  const state = globalThis[Symbol.for('breezeInspectionReadSchemas')];
  if (!state?.enabled) return JSON.stringify({state:'capture_paused',links:[]});
  try {
    const response = await fetch(url.href, {method:'GET',credentials:'same-origin',
      redirect:'manual',cache:'no-store',signal:AbortSignal.timeout(10000)});
    const stop = async result => {if(response.body) await response.body.cancel(); return JSON.stringify({...result,links:[]});};
    if (response.type === 'opaqueredirect') return stop({state:'redirect_unresolved'});
    if (!response.ok) return stop({state:response.status===401?'login_required':response.status===403?'permission_denied':'request_failed',http_status:response.status});
    const mime = (response.headers.get('Content-Type') || '').split(';')[0].toLowerCase().trim();
    if (mime !== 'text/html' || /attachment/i.test(response.headers.get('Content-Disposition') || '')) {
      return stop({state:'non_html_or_attachment',http_status:response.status});
    }
    const reader = response.body?.getReader();
    if (!reader) return JSON.stringify({state:'body_unavailable',links:[]});
    const decoder = new TextDecoder(); let bytes=0; let html='';
    while (state.enabled) {
      const chunk = await reader.read(); if(chunk.done) break;
      bytes += chunk.value.length;
      if(bytes>2*1024*1024) {await reader.cancel();return JSON.stringify({state:'too_large',links:[]});}
      html += decoder.decode(chunk.value,{stream:true});
    }
    if (!state.enabled) {await reader.cancel();return JSON.stringify({state:'capture_paused',links:[]});}
    html += decoder.decode();
    const scripts = []; let scriptTruncated=false;
    for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi)) {
      if (/\bsrc\s*=/i.test(match[1])) continue;
      if(scripts.length>=100) {scriptTruncated=true;break;}
      scripts.push({textContent:match[2]});
    }
    const links=[]; let linkTruncated=false;let anchorCount=0;
    for (const match of html.matchAll(/<a\b[^>]*>/gi)) {
      if(++anchorCount>20000) {linkTruncated=true;break;}
      const template=globalThis.document.createElement('template');template.innerHTML=match[0];
      const anchor=template.content.querySelector('a[href]');
      if(!anchor||anchor.hasAttribute('download')) continue;
      const href=anchor.getAttribute('href'); if(href.length>4096) continue;
      try {
        const link=new URL(href,url);
        if(link.origin!==expectedOrigin||link.username||link.password||Array.from(link.searchParams.keys()).some(k=>/token|secret|password|session|auth|^key$/i.test(k)))continue;
        link.hash='';links.push(link.href);
      } catch { /* Invalid anchors do not become navigation candidates. */ }
    }
    const document={querySelectorAll:()=>scripts};
    // PAGE_SCANNER
    const contracts=JSON.parse(inspectPageContracts());
    return JSON.stringify({state:'html_inspected',http_status:response.status,
      declarations:contracts.declarations,contract_truncated:scriptTruncated||contracts.truncated,
      tag_counts:reduceBreezeBody(html).tag_counts,links:Array.from(new Set(links)),
      truncated:linkTruncated,excluded_frames:0});
  } catch {return JSON.stringify({state:'request_failed',links:[]});}
}
