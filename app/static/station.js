import {badge, compare, grid, list, matrix, names, safe, tiers} from './cells.js';

const $ = selector => document.querySelector(selector);
const modules = {batches:'馆藏批次',manifest:'固化清单',mapping:'路由映射',fixity:'字节验签',drift:'副本漂移',reconcile:'迁移勾稽',archive:'复核封存'};
const tables = {catalogs:'批次版本',objects:'原件清单',routes:'映射规则',replicas:'副本记录'};
const data = {result:JSON.parse($('#initial').textContent), filter:'all', object:'0003', section:'drift', run:null, busy:false};

function notice(text, bad=false) {$('#feedback').textContent=text; $('#feedback').toggleAttribute('data-bad',bad);}
function itemHeader(row) {
  return `<div class="stamp"><strong>${safe(row.object_id)} · ${safe(row.path ?? row.raw.path)}</strong><code>${safe(row.sha256)}</code>
    ${list([['固化字节',row.bytes],['清单数据行',row.source_lines.join('、')]])}</div>`;
}
function inspect(row) {
  const {result,section} = data;
  if (section === 'archive') return vault();
  if (section === 'batches') return grid(['规则版本','生效','原行'],result.batches.rows.map(item=>[item.version,item.active?'是':'否',item.line]));
  if (section === 'reconcile') {
    const total = result.reconcile.totals;
    const stamp = `<div class="stamp"><strong>${total.originals} = ${total.verified} + ${total.pending} + ${total.conflict}</strong>${list([['已验副本',total.verified_copies],['可核字节',total.expected_bytes],['归类差异',total.difference]])}</div>`;
    const groups = result.drift.sharing ?? [];
    if (!groups.length) return stamp;
    return stamp+`<h3>共享副本组 · 留存一份物理占用</h3>`+grid(['共享组','共用馆号','留存馆号','阅览副本','冷存副本','归类'],
      groups.map(group=>[group.key,group.members.join('、'),group.keeper,group.copies.online,group.copies.vault,names[group.state]]));
  }
  if (!row) return '<p class="empty">选中原件查看证据。</p>';
  const head = itemHeader(row);
  if (section === 'manifest') return head+grid(['清单行','原始路径','申报摘要'],row.source_records.map(item=>[item.line,item.raw.path,item.raw.sha256]));
  if (section === 'mapping') return head+grid(['目标层','目标路径','路由行','判定'],row.copies.map(copy=>[tiers[copy.tier],copy.path,copy.route_lines.join('、'),copy.code ?? '映射命中']));
  if (section === 'fixity') return head+grid(['副本层','数据行','字节','观测摘要'],row.copies.flatMap(copy=>copy.history.map(observation=>[tiers[copy.tier],observation.line,observation.bytes,observation.sha256])));
  return head+compare(row);
}
function paint() {
  const {result,section} = data;
  const summary = result.reconcile.totals;
  const rows = result.drift.rows.filter(row=>data.filter==='all'||(data.filter==='shared'?Boolean(row.shared):row.state===data.filter));
  const current = rows.find(row=>row.object_id===data.object) ?? rows[0];
  data.object=current?.object_id;
  $('#metrics').innerHTML=[['原件',summary.originals,''],['两副本齐全',summary.verified,'verified'],['待补',summary.pending,'pending'],['冲突',summary.conflict,'conflict'],['已验副本',summary.verified_copies,'']].map(([label,value,className])=>`<div class="metric ${className}"><span>${label}</span><strong>${value}</strong></div>`).join('');
  $('#batch-name').textContent=result.batch; $('#policy').textContent=result.batches.selected ?? '无唯一规则';
  $('#matrix').innerHTML=matrix(rows,data.object); $('#matrix-count').textContent=`${rows.length} / ${summary.originals} 件原件`;
  $('#section-title').textContent=modules[section]; $('#inspector').innerHTML=inspect(current);
  const exceptions = section==='archive' || section==='drift' ? result.reconcile.issues : result[section].issues;
  const related = issue => current && (issue.object_id===current.object_id ||
    (issue.table==='objects' && current.source_lines.includes(issue.line)) ||
    current.copies.some(copy=>issue.table==='replicas' && copy.history.some(item=>item.line===issue.line)));
  const visible = $('#selected-only').checked ? exceptions.filter(related) : exceptions;
  $('#exceptions').innerHTML=grid(['来源','数据行','判定码','记录'],visible.map(issue=>[tables[issue.table],issue.line,issue.code,issue.detail]));
  $('#balance').textContent=result.reconcile.status==='MATCHED'?'原件归类已对平':'原件归类待复核';
  $('#batch-time').textContent=`${result.at} · ${result.ruleset}`;
  document.querySelectorAll('nav a').forEach(link=>{if(link.hash==='#'+section)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');});
}

function vault() {
  const run = data.run;
  if (!run) return '<p class="empty">运行验收后生成封存凭证。</p><button data-history>查询历史</button><div id="history"></div>';
  return `<div class="stamp"><strong>${safe(run.manifest.batch)}</strong><code>${safe(run.manifest.digest)}</code>${list([['生成时间',run.manifest.generated_at],['原件归类',run.result.reconcile.status==='MATCHED'?'已对平':'待复核']])}</div>
  <div class="review-actions"><button data-replay>复算快照</button><a class="file-link" href="/api/runs/${safe(run.id)}/export">下载封存证据</a><button data-history>查询历史</button></div>
  ${run.signature ? `<p>已封存 · ${safe(run.signature.reviewer)}</p>` : '<form class="receipt-entry" id="sign"><label>复核人 <input name="reviewer" maxlength="100" required></label><button>签署封存</button></form>'}<div id="history"></div>`;
}
async function request(path, payload) {
  const response = await fetch(path,payload===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const body = await response.json(); if(!response.ok) throw new Error(body.message||'验收请求失败，请重试。'); return body;
}
async function work(task) {
  if(data.busy)return; data.busy=true; notice('处理中…');
  try{await task();}catch(error){notice(error.message,true);}finally{data.busy=false;}
}
function useRun(run){data.run=run; data.result=run.result; paint();}
function route(){const section=location.hash.slice(1);data.section=modules[section]?section:'drift';paint();}
$('#controls').addEventListener('submit',event=>{event.preventDefault();work(async()=>{
  const run=data.run?await request(`/api/runs/${data.run.id}/rerun`,{}):await request('/api/runs',{sample:$('#sample').value});
  useRun(run);notice(run.reused?'复算一致':'验收已归档');
});});
$('#sample').addEventListener('change',event=>{location.href=`/?sample=${event.target.value}${location.hash}`;});
$('#filter').addEventListener('change',event=>{data.filter=event.target.value;paint();});
$('#selected-only').addEventListener('change',paint);
$('#matrix').addEventListener('click',event=>{const target=event.target.closest('[data-object]');if(!target)return;data.object=target.dataset.object;paint();$('#matrix').querySelector('[aria-pressed=true]')?.focus({preventScroll:true});});
$('#open-source').addEventListener('click',()=>$('#source-file').click());
$('#source-file').addEventListener('change',event=>{const [file]=event.target.files;if(!file)return;work(async()=>{
  let source;try{source=JSON.parse(await file.text());}catch{throw new Error('清单格式错误，选择 JSON 文件。');}
  useRun(await request('/api/runs',{source}));notice('清单验收已归档');
}).finally(()=>{event.target.value='';});});
$('#inspector').addEventListener('click',event=>{
  const button=event.target.closest('[data-replay],[data-history],[data-run]');if(!button)return;
  work(async()=>{
    if(button.hasAttribute('data-replay')){useRun(await request(`/api/runs/${data.run.id}/rerun`,{}));notice('复算一致');}
    if(button.hasAttribute('data-history')){const {runs}=await request('/api/runs');$('#history').replaceChildren(...runs.map(run=>{const item=document.createElement('button');item.dataset.run=run.id;item.textContent=run.batch;return item;}));notice(runs.length?`${runs.length} 笔封存记录`:'暂无封存记录');}
    if(button.dataset.run){useRun(await request(`/api/runs/${button.dataset.run}`));notice('已载入封存记录');}
  });
});
$('#inspector').addEventListener('submit',event=>{if(event.target.id!=='sign')return;event.preventDefault();work(async()=>{
  data.run.signature=await request(`/api/runs/${data.run.id}/sign`,{reviewer:new FormData(event.target).get('reviewer'),digest:data.run.manifest.digest});
  paint();notice('复核签署完成');
});});
addEventListener('hashchange',route);route();
