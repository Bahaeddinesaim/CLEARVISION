PREMIUM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;800;900&display=swap');
:root{
  --cv-bg:#eef3fb;--cv-shell:#f8fbff;--cv-panel:rgba(255,255,255,.86);--cv-panel-2:#f3f6fb;
  --cv-ink:#101828;--cv-muted:#667085;--cv-faint:#98a2b3;--cv-line:rgba(16,24,40,.10);
  --cv-blue:#4f8ef7;--cv-violet:#7c5ff5;--cv-green:#12b76a;--cv-red:#f04438;--cv-amber:#f79009;
  --cv-shadow:0 18px 50px rgba(16,24,40,.10);--cv-shadow-2:0 28px 90px rgba(79,142,247,.18);
}
html,body,.stApp,[class*="css"]{font-family:'DM Sans',system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}
.stApp{
  background:
    linear-gradient(135deg,rgba(79,142,247,.12),transparent 26%),
    linear-gradient(315deg,rgba(45,212,160,.13),transparent 24%),
    var(--cv-bg);
  color:var(--cv-ink);
}
.block-container{max-width:1420px;padding:1rem 1.25rem 4.5rem;}
[data-testid="stHeader"]{background:rgba(238,243,251,.74);backdrop-filter:blur(20px);border-bottom:1px solid var(--cv-line);}
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#0a0c10 0%,#0f1218 48%,#161b24 100%);
  border-right:1px solid rgba(255,255,255,.08);padding-top:.65rem;
}
section[data-testid="stSidebar"] *{color:#e8eaf0!important;}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3{font-size:15px;font-weight:800;letter-spacing:-.2px;}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#8b92a5!important;font-size:11px;}
section[data-testid="stSidebar"] [data-testid="stRadio"] label{min-height:38px;border-radius:11px;padding:.32rem .65rem;margin:.06rem 0;color:#8b92a5!important;}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{background:#1c2230;color:#fff!important;}
section[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.08);}
.cv-topbar{
  display:flex;align-items:center;justify-content:space-between;gap:16px;padding:15px 18px;margin-bottom:14px;
  background:rgba(255,255,255,.72);border:1px solid var(--cv-line);border-radius:18px;
  box-shadow:var(--cv-shadow);backdrop-filter:blur(20px);
}
.cv-page-title{font-size:18px;font-weight:900;letter-spacing:-.2px;color:var(--cv-ink);}
.cv-page-subtitle{font-size:12px;color:var(--cv-faint);margin-top:2px;}
.cv-actions{display:flex;align-items:center;gap:9px;flex-wrap:wrap;justify-content:flex-end;}
.cv-live{display:inline-flex;align-items:center;gap:7px;padding:7px 11px;border-radius:999px;background:rgba(18,183,106,.10);border:1px solid rgba(18,183,106,.22);color:var(--cv-green);font-size:12px;font-weight:800;}
.cv-live i{width:7px;height:7px;border-radius:999px;background:var(--cv-green);box-shadow:0 0 0 4px rgba(18,183,106,.13);}
.cv-action{display:inline-flex;padding:8px 12px;border-radius:11px;font-size:12px;font-weight:800;border:1px solid var(--cv-line);}
.cv-action.secondary{background:var(--cv-panel-2);color:var(--cv-muted);}.cv-action.primary{background:var(--cv-blue);color:white;border-color:rgba(79,142,247,.25);}
.app-hero{
  position:relative;overflow:hidden;margin-bottom:16px;border-radius:22px;padding:22px 22px;
  background:
    linear-gradient(135deg,rgba(10,12,16,.95),rgba(22,27,36,.92) 48%,rgba(79,142,247,.88)),
    #0f1218;
  color:white;border:1px solid rgba(255,255,255,.12);box-shadow:var(--cv-shadow-2);
}
.app-hero:after{content:"";position:absolute;right:-90px;bottom:-130px;width:340px;height:340px;border-radius:999px;background:radial-gradient(circle,rgba(45,212,160,.32),transparent 60%);}
.hero-grid{position:relative;display:grid;grid-template-columns:minmax(0,1.35fr) minmax(240px,.65fr);gap:20px;align-items:end;z-index:1;}
.eyebrow{display:inline-flex;align-items:center;gap:7px;font-size:10px;font-weight:900;letter-spacing:.1em;text-transform:uppercase;color:#8ec5ff;background:rgba(79,142,247,.16);border:1px solid rgba(79,142,247,.24);padding:5px 10px;border-radius:999px;}
.app-hero h1{font-size:clamp(28px,4.4vw,52px);line-height:.98;margin:12px 0 8px;font-weight:900;letter-spacing:0;color:white;}
.app-hero p{max-width:760px;margin:0;color:rgba(232,234,240,.78);font-size:14px;line-height:1.55;}
.hero-status{display:grid;gap:8px;}
.status-chip{display:flex;justify-content:space-between;gap:10px;padding:10px 12px;border-radius:13px;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.12);backdrop-filter:blur(18px);}
.status-chip span{font-size:11px;color:rgba(232,234,240,.62);}.status-chip b{font-size:13px;color:white;font-weight:900;}
.cv-nav-shell{margin:2px 0 18px;}
.cv-nav-label{font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.08em;color:var(--cv-faint);margin:0 0 8px 2px;}
.cv-nav-scroll{
  display:flex;gap:12px;overflow-x:auto;overflow-y:hidden;padding:2px 2px 13px;scroll-snap-type:x proximity;
  scrollbar-width:thin;scrollbar-color:rgba(79,142,247,.45) transparent;
}
.cv-nav-scroll::-webkit-scrollbar{height:7px}.cv-nav-scroll::-webkit-scrollbar-track{background:transparent}.cv-nav-scroll::-webkit-scrollbar-thumb{background:rgba(79,142,247,.40);border-radius:999px;}
.cv-nav-card{
  position:relative;min-width:210px;max-width:210px;min-height:118px;padding:15px 15px 14px;border-radius:20px;text-decoration:none!important;
  background:rgba(255,255,255,.76);border:1px solid var(--cv-line);box-shadow:var(--cv-shadow);overflow:hidden;scroll-snap-align:start;
  transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease;
}
.cv-nav-card:before{content:"";position:absolute;right:-34px;top:-38px;width:112px;height:112px;border-radius:999px;opacity:.18;}
.cv-nav-card:after{content:"";position:absolute;left:14px;bottom:12px;width:42px;height:3px;border-radius:999px;opacity:.72;}
.cv-nav-card:hover{transform:translateY(-4px);box-shadow:0 26px 78px rgba(16,24,40,.16);border-color:rgba(79,142,247,.24);}
.cv-nav-card.active{border-color:rgba(79,142,247,.52);box-shadow:0 28px 90px rgba(79,142,247,.20);}
.cv-nav-card strong{position:relative;display:block;font-size:15px;line-height:1.1;color:var(--cv-ink);font-weight:900;margin-top:18px;}
.cv-nav-card small{position:relative;display:block;font-size:12px;line-height:1.35;color:var(--cv-muted);margin-top:7px;}
.cv-nav-num{position:relative;display:inline-grid;place-items:center;width:30px;height:30px;border-radius:10px;font-size:11px;font-weight:900;}
.cv-nav-card.blue .cv-nav-num{background:rgba(79,142,247,.13);color:var(--cv-blue)}.cv-nav-card.blue:before,.cv-nav-card.blue:after{background:var(--cv-blue)}
.cv-nav-card.green .cv-nav-num{background:rgba(18,183,106,.13);color:var(--cv-green)}.cv-nav-card.green:before,.cv-nav-card.green:after{background:var(--cv-green)}
.cv-nav-card.violet .cv-nav-num{background:rgba(124,95,245,.13);color:var(--cv-violet)}.cv-nav-card.violet:before,.cv-nav-card.violet:after{background:var(--cv-violet)}
.cv-nav-card.amber .cv-nav-num{background:rgba(247,144,9,.13);color:var(--cv-amber)}.cv-nav-card.amber:before,.cv-nav-card.amber:after{background:var(--cv-amber)}
.cv-nav-card.red .cv-nav-num{background:rgba(240,68,56,.13);color:var(--cv-red)}.cv-nav-card.red:before,.cv-nav-card.red:after{background:var(--cv-red)}
.section-title{font-size:17px;font-weight:900;letter-spacing:-.1px;margin:16px 0 8px;color:var(--cv-ink);}
.section-subtitle{font-size:13px;color:var(--cv-muted);margin:-3px 0 12px;line-height:1.45;}
.kpi-card,.glass-card,.insight-card,.cv-panel{
  background:var(--cv-panel);border:1px solid var(--cv-line);border-radius:18px;box-shadow:var(--cv-shadow);backdrop-filter:blur(20px);
}
.kpi-card{position:relative;overflow:hidden;min-height:126px;padding:16px 17px;transition:transform .18s ease,box-shadow .18s ease;}
.kpi-card:before{content:"";position:absolute;inset:0;background:linear-gradient(135deg,rgba(79,142,247,.12),transparent 42%);opacity:.75;}
.kpi-card:after{content:"";position:absolute;right:-20px;top:-24px;width:88px;height:88px;border-radius:999px;background:rgba(124,95,245,.12);}
.kpi-card:hover{transform:translateY(-4px);box-shadow:0 24px 70px rgba(79,142,247,.18);}
.kpi-top,.kpi-value,.kpi-sub{position:relative;z-index:1;}
.kpi-top{display:flex;align-items:center;justify-content:space-between;gap:10px;}
.kpi-icon{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:rgba(79,142,247,.12);color:var(--cv-blue);font-size:12px;font-weight:900;}
.kpi-label{font-size:11px;color:var(--cv-muted);font-weight:800;text-transform:uppercase;letter-spacing:.04em;}
.kpi-value{font-size:30px;line-height:1;margin-top:13px;color:var(--cv-ink);font-weight:900;letter-spacing:0;}
.kpi-sub{font-size:12px;color:var(--cv-faint);margin-top:8px;}
.cv-panel{padding:18px;min-height:100%;}
.cv-card-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:16px;}
.cv-card-head span{font-size:13px;font-weight:900;color:var(--cv-ink);}.cv-card-head b{font-size:11px;color:var(--cv-faint);font-weight:800;}.cv-card-head .ok{color:var(--cv-green);}
.cv-score-ring{position:relative;width:128px;height:128px;margin:4px auto 10px;}
.cv-score-ring svg{width:128px;height:128px;transform:rotate(-90deg);}
.cv-score-ring circle{fill:none;stroke-width:9;cx:50;cy:50;r:40;stroke-dasharray:251.2;stroke-linecap:round;}
.ring-bg{stroke:rgba(16,24,40,.08);}.ring-fg{stroke:var(--cv-green);filter:drop-shadow(0 0 8px rgba(18,183,106,.25));}
.cv-score-number{position:absolute;inset:0;display:grid;place-items:center;text-align:center;}
.cv-score-number strong{display:block;font-size:30px;line-height:1;color:var(--cv-green);}.cv-score-number span{display:block;font-size:11px;color:var(--cv-faint);}
.cv-grade{width:max-content;margin:8px auto 4px;padding:5px 15px;border-radius:999px;background:rgba(18,183,106,.12);color:var(--cv-green);font-size:12px;font-weight:900;}
.cv-risk{text-align:center;font-size:11.5px;color:var(--cv-faint);margin-bottom:14px;}
.cv-bar-row{display:flex;align-items:center;gap:9px;margin:9px 0;}.cv-bar-label{width:86px;font-size:11.5px;color:var(--cv-muted);}
.cv-bar-track{flex:1;height:6px;border-radius:999px;background:rgba(16,24,40,.08);overflow:hidden;}.cv-bar-fill{height:100%;border-radius:999px;}
.cv-bar-fill.green{background:var(--cv-green)}.cv-bar-fill.blue{background:var(--cv-blue)}.cv-bar-fill.violet{background:var(--cv-violet)}.cv-bar-fill.amber{background:var(--cv-amber)}
.cv-bar-value{width:36px;text-align:right;font-size:11px;color:var(--cv-faint);font-weight:800;}
.cv-det-row,.cv-anom-row{display:flex;align-items:center;gap:11px;padding:10px 0;border-bottom:1px solid var(--cv-line);}
.cv-det-row:last-child,.cv-anom-row:last-child{border-bottom:0;}
.cv-det-icon{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;font-size:11px;font-weight:900;flex:0 0 auto;}
.cv-det-icon.blue{background:rgba(79,142,247,.12);color:var(--cv-blue)}.cv-det-icon.green{background:rgba(18,183,106,.12);color:var(--cv-green)}.cv-det-icon.violet{background:rgba(124,95,245,.12);color:var(--cv-violet)}.cv-det-icon.amber{background:rgba(247,144,9,.12);color:var(--cv-amber)}
.cv-det-info{min-width:0;flex:1;}.cv-det-name{font-size:13px;color:var(--cv-ink);font-weight:800;}.cv-det-sub{font-size:11px;color:var(--cv-faint);margin-top:1px;}
.cv-det-count{font-size:14px;font-weight:900;color:var(--cv-ink);}.cv-conf{font-size:10.5px;font-weight:900;color:var(--cv-green);background:rgba(18,183,106,.11);padding:3px 8px;border-radius:999px;}
.cv-sev{font-size:10px;font-weight:900;padding:3px 8px;border-radius:999px;align-self:flex-start;margin-top:1px;}
.cv-sev.critical,.cv-sev.high{background:rgba(240,68,56,.12);color:var(--cv-red)}.cv-sev.medium{background:rgba(247,144,9,.13);color:var(--cv-amber)}.cv-sev.low{background:rgba(18,183,106,.12);color:var(--cv-green)}
.cv-anom-row{align-items:flex-start;}.cv-anom-title{font-size:13px;color:var(--cv-ink);font-weight:900;}.cv-anom-desc{font-size:12px;color:var(--cv-muted);line-height:1.35;margin-top:2px;}.cv-anom-meta{font-size:11px;color:var(--cv-faint);margin-top:4px;}
.cv-pipe-row{display:flex;justify-content:space-between;align-items:center;padding:10px 11px;border-radius:12px;background:var(--cv-panel-2);margin-bottom:8px;}
.cv-pipe-row span{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:900;color:var(--cv-ink);}.cv-pipe-row b{font-size:11px;color:var(--cv-faint);}
.cv-pipe-row i{width:7px;height:7px;border-radius:999px;display:inline-block;}.cv-pipe-row i.green{background:var(--cv-green)}.cv-pipe-row i.blue{background:var(--cv-blue)}.cv-pipe-row i.violet{background:var(--cv-violet)}.cv-pipe-row i.amber{background:var(--cv-amber)}
.cv-catalog{border-top:1px solid var(--cv-line);padding-top:14px;margin-top:12px;display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;}
.cv-catalog span{font-size:12px;color:var(--cv-muted);}.cv-catalog b{font-size:12px;color:var(--cv-ink);}.cv-wide-track{grid-column:1 / -1;height:7px;border-radius:999px;background:rgba(16,24,40,.08);overflow:hidden;}.cv-wide-track div{height:100%;background:linear-gradient(90deg,var(--cv-blue),var(--cv-green));}
.glass-card{padding:18px;margin-bottom:14px;}.soft-text{color:var(--cv-muted);font-size:13px;line-height:1.55;}
.badge{display:inline-flex;align-items:center;padding:4px 9px;border-radius:999px;font-size:10.5px;font-weight:900;margin:2px;background:rgba(79,142,247,.12);color:var(--cv-blue);}
.danger{background:rgba(240,68,56,.12);color:var(--cv-red)}.success{background:rgba(18,183,106,.11);color:var(--cv-green)}.warn{background:rgba(247,144,9,.12);color:var(--cv-amber)}.violet{background:rgba(124,95,245,.12);color:var(--cv-violet)}
.anomaly-table table{width:100%;border-collapse:collapse;background:var(--cv-panel);border:1px solid var(--cv-line);border-radius:18px;overflow:hidden;box-shadow:var(--cv-shadow);}
.anomaly-table th{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--cv-faint);font-weight:900;background:var(--cv-panel-2);padding:10px;text-align:left;}
.anomaly-table td{font-size:12px;color:var(--cv-ink);border-top:1px solid var(--cv-line);padding:11px;vertical-align:top;}
.mobile-nav{display:none;margin:0 0 12px;}
.stButton>button,.stDownloadButton>button{border-radius:12px!important;border:1px solid rgba(79,142,247,.25)!important;background:var(--cv-blue)!important;color:#fff!important;font-weight:900!important;box-shadow:0 14px 30px rgba(79,142,247,.20)!important;padding:.6rem .95rem!important;font-size:12.5px!important;}
.stButton>button:hover,.stDownloadButton>button:hover{background:#3d7ef0!important;transform:translateY(-1px);}
[data-testid="stFileUploader"]{background:var(--cv-panel);border:1px dashed rgba(79,142,247,.45);border-radius:18px;padding:14px;box-shadow:var(--cv-shadow);}
[data-testid="stDataFrame"]{border-radius:18px;overflow:hidden;border:1px solid var(--cv-line);box-shadow:var(--cv-shadow);}
div[data-testid="stTabs"] button{border-radius:999px;font-size:12px;}
@media(max-width:760px){
  .block-container{padding:.7rem .75rem 5rem;}.cv-topbar{display:block;padding:14px}.cv-actions{justify-content:flex-start;margin-top:10px;}
  .hero-grid{grid-template-columns:1fr}.app-hero{padding:18px;border-radius:20px}.app-hero h1{font-size:30px;}
  .hero-status{grid-template-columns:repeat(3,1fr)}.status-chip{display:block}.status-chip b{display:block;margin-top:2px;}
  .kpi-card{min-height:110px}.kpi-value{font-size:25px}.mobile-nav{display:block;}section[data-testid="stSidebar"]{display:none;}
}
</style>
"""

DARK_CSS = """
<style>
:root{
  --cv-bg:#0a0c10;--cv-shell:#0f1218;--cv-panel:rgba(15,18,24,.88);--cv-panel-2:#161b24;
  --cv-ink:#e8eaf0;--cv-muted:#8b92a5;--cv-faint:#525b6e;--cv-line:rgba(255,255,255,.09);
  --cv-shadow:none;--cv-shadow-2:0 28px 90px rgba(0,0,0,.35);
}
.stApp{background:radial-gradient(circle at 80% 0%,rgba(79,142,247,.16),transparent 30%),var(--cv-bg)!important;color:var(--cv-ink)!important;}
[data-testid="stHeader"]{background:rgba(10,12,16,.78)!important;border-bottom:1px solid var(--cv-line)!important;}
.cv-topbar,.cv-panel,.kpi-card,.glass-card,.app-hero{background:var(--cv-panel)!important;border-color:var(--cv-line)!important;color:var(--cv-ink)!important;}
.cv-page-title,.cv-card-head span,.cv-det-name,.cv-det-count,.cv-pipe-row span,.cv-catalog b,.kpi-value,.section-title,.anomaly-table td{color:var(--cv-ink)!important;}
.cv-page-subtitle,.cv-card-head b,.cv-det-sub,.cv-pipe-row b,.kpi-label,.kpi-sub,.section-subtitle,.soft-text,.cv-anom-desc,.cv-anom-meta{color:var(--cv-muted)!important;}
.cv-pipe-row,.cv-action.secondary,.status-chip{background:var(--cv-panel-2)!important;border-color:var(--cv-line)!important;}
.cv-nav-card{background:rgba(15,18,24,.86)!important;border-color:var(--cv-line)!important;box-shadow:none!important;}
.cv-nav-card strong{color:var(--cv-ink)!important}.cv-nav-card small,.cv-nav-label{color:var(--cv-muted)!important}
.cv-nav-card.active{border-color:rgba(79,142,247,.52)!important;background:linear-gradient(135deg,rgba(79,142,247,.14),rgba(15,18,24,.90))!important;}
.ring-bg,.cv-bar-track,.cv-wide-track{background:rgba(255,255,255,.08)!important;stroke:rgba(255,255,255,.08)!important;}
.anomaly-table table{background:var(--cv-panel)!important;border-color:var(--cv-line)!important;box-shadow:none!important;}
.anomaly-table th{background:var(--cv-panel-2)!important;color:var(--cv-faint)!important;}
.anomaly-table td{border-top-color:var(--cv-line)!important;}
[data-testid="stFileUploader"],[data-testid="stDataFrame"]{background:var(--cv-panel)!important;border-color:var(--cv-line)!important;box-shadow:none!important;}
</style>
"""
