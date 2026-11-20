"""Inject a reversible, branch-only 3.2 reflow fix without suppressing data.
Charts/tables requiring 2D layout gain keyboard-focusable horizontal scrolling
inside their own labelled regions; no global clipping of axis labels.
"""
from pathlib import Path
import hashlib
import sys
p=Path("index.html")
original=p.read_text(encoding="utf-8")
marker="ncd-v32-reflow-scroll"
if marker in original:
    print("v3.2 already present")
    sys.exit(0)
at=original.lower().find("</head>")
if at<0:
    raise SystemExit("No closing </head>; refusing modification")
addition=r'''
<!-- ncd-v32-reflow-scroll -->
<style id="ncd-v32-reflow-scroll">
.ncd-accessible-scroll {display:block;width:100%;max-width:100%;min-width:0;position:relative}
@media (max-width:240px) {
  #explorer .ncd-accessible-scroll, #quality .ncd-accessible-scroll {
    overflow-x:auto!important;overflow-y:hidden!important;
    overscroll-behavior-x:contain;scrollbar-width:auto;
    -webkit-overflow-scrolling:touch;
    outline-offset:2px;
  }
  #explorer .ncd-accessible-scroll:focus-visible,
  #quality .ncd-accessible-scroll:focus-visible {outline:2px solid #135fbe;}
  #explorer .ncd-accessible-scroll > .js-plotly-plot {
    min-width:365px!important;width:365px!important;max-width:none!important;
    flex:0 0 365px;
  }
  #explorer .ncd-accessible-scroll > .js-plotly-plot .plot-container {
    min-width:365px!important;max-width:none!important;
  }
    #explorer, #quality {min-width:0;max-width:100%}
}
@media (max-width:400px) {
  #quality .ncd-accessible-scroll {overflow-x:auto!important;overflow-y:hidden!important;contain:layout paint inline-size;inline-size:100%!important;max-inline-size:100%!important;}
  #quality .ncd-accessible-scroll > table {min-width:0!important;max-width:100%!important;width:100%!important;table-layout:fixed!important;}
  #quality .ncd-accessible-scroll th, #quality .ncd-accessible-scroll td {white-space:normal!important;overflow-wrap:anywhere!important;word-break:normal!important;}
}
</style>
<script id="ncd-v32-region-init">
(function(){
'use strict';
function ensureRegions(){
  var candidates=[
    ['#explorer #heatmap','Interactive heatmap; scroll horizontally to read all labels'],
    ['#explorer #change','Change comparison chart; scroll horizontally to read all labels']
  ];
  document.querySelectorAll('#quality table').forEach(function(node,i){
    candidates.push([node,'Data quality table '+(i+1)+'; scroll horizontally to read all columns']);
  });
  candidates.forEach(function(entry) {
    var node=typeof entry[0]==='string'?document.querySelector(entry[0]):entry[0];
    if(!node || node.parentElement.classList.contains('ncd-accessible-scroll'))return;
    var region=document.createElement('div');
    region.className='ncd-accessible-scroll';
    region.setAttribute('role','region');
    region.setAttribute('aria-label',entry[1]);
    region.tabIndex=0;
    node.parentNode.insertBefore(region,node);
    region.appendChild(node);
  });
}
function initialize(){
  ensureRegions();
  var observer=new MutationObserver(function(){ensureRegions();});
  ['explorer','quality'].forEach(function(id){
    var node=document.getElementById(id);
    if(node)observer.observe(node,{childList:true,subtree:true});
  });
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize,{once:true});
else initialize();
})();
</script>
'''
new=original[:at]+addition+original[at:]
p.write_text(new,encoding="utf-8")
print("v3.2 patch bytes",len(new)-len(original),
      "sha256_after",hashlib.sha256(new.encode()).hexdigest())
