"""Idempotently inject responsive layout rules into the source HTML.

The original 4.87 MB source is retained byte-for-byte except for the injection
immediately before </head>. No live or deployed website is edited.
"""
from pathlib import Path

p = Path("index.html")
raw = p.read_text(encoding="utf-8")
marker = "ncd-responsive-fix-v1"
if marker in raw:
    raise SystemExit("Responsive fix already present; refusing duplicate injection.")
head = raw.lower().find("</head>")
if head == -1:
    raise SystemExit("Cannot locate HTML head; source unchanged.")

injection = r"""
<!-- ncd-responsive-fix-v1 -->
<style id="ncd-responsive-fix-v1">
html, body {max-width:100%; overflow-x:clip;}
*, *::before, *::after {box-sizing:border-box;}
#overview, #explorer, #quality,
#overview *, #explorer *, #quality * {min-width:0;}
#overview, #explorer, #quality {max-width:100%; overflow-x:clip;}
#overview > *, #explorer > *, #quality > * {max-width:100%;}
#overview .js-plotly-plot, #explorer .js-plotly-plot,
#quality .js-plotly-plot {
  display:block; width:100%!important; max-width:100%!important;
  min-width:0!important; position:relative; margin-top:32px;
}
#overview .plot-container, #explorer .plot-container,
#quality .plot-container {max-width:100%; min-width:0;}
#overview .modebar-container, #explorer .modebar-container,
#quality .modebar-container {top:-30px!important; right:0!important;}
@media (max-width:900px) {
  #overview, #explorer, #quality {width:100%; min-width:0;}
  #overview .js-plotly-plot, #explorer .js-plotly-plot,
  #quality .js-plotly-plot {margin-top:36px;}
  #overview .modebar-container, #explorer .modebar-container,
  #quality .modebar-container {top:-34px!important;}
}
</style>
<script id="ncd-responsive-resizer">
(function () {
  'use strict';
  let queued=false;
  function resize() {
    queued=false;
    if (!window.Plotly || !window.Plotly.relayout) return;
    document.querySelectorAll('#overview .js-plotly-plot, #explorer .js-plotly-plot, #quality .js-plotly-plot').forEach(function(plot) {
      if (!plot.offsetParent || !plot._fullLayout) return;
      const parent=plot.parentElement;
      if (!parent) return;
      const rect=parent.getBoundingClientRect();
      const width=Math.floor(Math.min(rect.width, document.documentElement.clientWidth - Math.max(rect.left,0) - 8));
      if (!Number.isFinite(width) || width < 230) return;
      const current=plot._fullLayout.width;
      if (Math.abs(current-width) > 2) {
        window.Plotly.relayout(plot, {width:width}).catch(function(e){console.warn('NCD resize:',e);});
      }
    });
  }
  function schedule() {
    if (queued) return;
    queued=true;
    requestAnimationFrame(function(){requestAnimationFrame(resize);});
  }
  document.addEventListener('DOMContentLoaded',function() {
    window.addEventListener('resize',schedule,{passive:true});
    document.querySelectorAll('[id^="tab-"]').forEach(function(tab){
      tab.addEventListener('click',function(){setTimeout(schedule,120);setTimeout(schedule,500);});
    });
    const ro=window.ResizeObserver ? new ResizeObserver(schedule) : null;
    if(ro) ['overview','explorer','quality'].forEach(function(id){
      const node=document.getElementById(id);if(node)ro.observe(node);
    });
    setTimeout(schedule,300);setTimeout(schedule,1500);
  });
})();
</script>
"""
p.write_text(raw[:head] + injection + raw[head:], encoding="utf-8")
print("Patched",p,"source bytes",len(raw.encode()),"patched bytes",p.stat().st_size)
