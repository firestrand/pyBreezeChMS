/* Fixed pagination checks; no real DOM, records or network requests. */
(() => {
  let clicked = 0;
  const make = (text, disabled = false, type = 'button') => ({
    textContent: text, disabled, tagName: 'BUTTON',
    getAttribute: key => key === 'type' ? type : null,
    getClientRects: () => [1], closest: () => null,
    click: () => {clicked++;}
  });
  const next = make('Next');
  const submit = make('Next', false, 'submit');
  const privateRecord = make('SYNTHETIC_PRIVATE_PERSON');
  const region = {querySelectorAll: () => [next, submit, privateRecord]};
  const document = {querySelectorAll: () => [region]};
  // LIST_SCANNER
  const first = JSON.parse(inspectBreezeListControls(true));
  next.disabled = true;
  const last = JSON.parse(inspectBreezeListControls(true));
  const checks = {
    next_advanced_once: first.advanced && clicked === 1,
    no_submit_click: first.controls.some(c => !c.actionable),
    disabled_next_stops: !last.advanced,
    no_record_text: !JSON.stringify([first,last]).includes('SYNTHETIC_PRIVATE')
  };
  return JSON.stringify({checks, passed: Object.values(checks).every(Boolean)});
})()
