export const names = {verified:'已验',pending:'待补',conflict:'冲突',unavailable:'隔离',shared:'共享'};
export const tiers = {online:'阅览副本',vault:'冷存副本'};
export const safe = value => String(value ?? '—').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
export const badge = (state, text) => `<span class="flag ${safe(state)}">${safe(text ?? names[state])}</span>`;
export const grid = (headers, rows) => rows.length ? `<table><thead><tr>${headers.map(value=>`<th>${safe(value)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(value=>`<td>${safe(value)}</td>`).join('')}</tr>`).join('')}</tbody></table>` : '<p class="empty">暂无对应记录。</p>';
export const list = entries => `<dl>${entries.map(([key,value])=>`<dt>${safe(key)}</dt><dd>${safe(value)}</dd>`).join('')}</dl>`;

export function matrix(rows, selected) {
  if (!rows.length) return '<p class="empty">当前筛选没有原件。</p>';
  return `<table class="matrix-table" aria-label="副本验收矩阵"><thead><tr class="column-key"><th></th><th>A</th><th>B</th><th>C</th><th>D</th><th>E</th></tr>
    <tr><th class="num">行</th><th>馆号</th><th>原件</th><th>阅览</th><th>冷存</th><th>归类</th></tr></thead><tbody>${rows.map(row=>{
    const item = tier => badge(row.copies.find(copy=>copy.tier===tier)?.state ?? 'unavailable');
    const active = row.object_id === selected;
    return `<tr class="${active?'chosen':''}"><td class="num line-index">${row.line}</td><td><button class="obj-button" data-object="${safe(row.object_id)}" aria-pressed="${active}">${safe(row.object_id)}</button>${row.shared?badge('shared'):''}</td>
      <td class="filename" title="${safe(row.path ?? row.raw.path)}">${safe(String(row.path ?? row.raw.path ?? '').split('/').at(-1))}</td><td>${item('online')}</td><td>${item('vault')}</td><td>${badge(row.state,row.state==='verified'?'齐全':names[row.state])}</td></tr>`;
  }).join('')}</tbody></table>`;
}

export function compare(row) {
  if (!row.copies.length) return '<p class="empty">清单问题待复核。</p>';
  const share = row.shared ? `<div class="stamp"><strong>共享副本组 ${safe(row.shared.key)} · 一份物理占用</strong>${list([['共用馆号',row.shared.members.join('、')],['留存馆号',row.shared.keeper],['本馆号持有副本',row.shared.holds_copy?'是':'否，回查至 '+row.shared.keeper]])}</div>` : '';
  return share+'<div class="paired">'+row.copies.map(copy=>`<article class="copy"><h3>${tiers[copy.tier]} ${badge(copy.state)} ${copy.shared?badge('shared','共享副本'):''}</h3>
    <p class="path">${safe(copy.path)}</p><code class="${copy.state==='conflict'?'mismatch':''}">${safe(copy.sha256)}</code>
    ${list([['判定',copy.code ?? '摘要一致'],['实测字节',copy.bytes],['路由行',copy.route_lines.join('、') || '—'],['副本行',copy.replica_lines.join('、') || '—'],['观测时刻',copy.observed]])}</article>`).join('')+'</div>';
}
