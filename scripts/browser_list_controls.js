/* Inspect/click only conventional pagination controls; never return record text. */
function inspectBreezeListControls(advance = false) {
  const selectors = ['.pagination','.pager','.dataTables_paginate',
    '[aria-label="Pagination"]','[aria-label="pagination"]','#pagination'];
  const regions = Array.from(new Set(selectors.flatMap(s => Array.from(document.querySelectorAll(s)))));
  const candidates = Array.from(new Set(regions.flatMap(r => Array.from(r.querySelectorAll('a,button')))));
  const controls = candidates.flatMap(element => {
    if (!element.getClientRects().length) return [];
    const raw = (element.getAttribute('aria-label') || element.getAttribute('title') || element.textContent || '').replace(/\s+/g,' ').trim();
    let label = null;
    if (/^(next(?: page)?(?:\s*[»›>]+)?|[»›>])$/i.test(raw)) label = 'next';
    if (/^(previous(?: page)?(?:\s*[«‹<]+)?|prev|[«‹<])$/i.test(raw)) label = 'previous';
    if (/^(first|last)(?: page)?$/i.test(raw)) label = raw.toLowerCase().split(' ')[0];
    if (!label) return [];
    const disabled = !!element.disabled || element.getAttribute('aria-disabled') === 'true' || !!element.closest('.disabled');
    const actionable = element.tagName === 'A' || element.getAttribute('type') === 'button';
    return [{element, label, disabled, actionable}];
  });
  let advanced = false;
  if (advance) {
    const next = controls.find(c => c.label === 'next' && !c.disabled && c.actionable);
    if (next) { next.element.click(); advanced = true; }
  }
  return JSON.stringify({regions: regions.length, controls: controls.slice(0, 30).map(c => ({
    label: c.label, disabled: c.disabled, actionable: c.actionable
  })), advanced});
}
