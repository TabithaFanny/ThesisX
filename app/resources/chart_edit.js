/**
 * chart_edit.js — 图表动态编辑系统
 *
 * 提供21种图表的SVG渲染器和双击编辑弹窗。
 * 用户双击图表后弹出数据编辑面板，修改后实时重绘SVG。
 */
(function() {
'use strict';

var COLORS = ['#4A90D9','#27AE60','#F39C12','#E74C3C','#9B59B6','#1ABC9C',
              '#3498DB','#2ECC71','#E67E22','#C0392B','#8E44AD','#16A085'];
var W = 500, H = 300, PAD = {t:42,r:30,b:40,l:60};
var FONT = "'Microsoft YaHei',sans-serif";

// ── Utility ──
function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function cx(i,n,l,r) { return l + (r-l) * (i + 0.5) / n; }
function lerp(v,min,max,lo,hi) { return lo + (hi-lo) * (v-min) / (max-min||1); }

function titleSvg(title, x, y) {
    return '<text data-ce="title" x="'+x+'" y="'+y+'" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="'+FONT+'">'+esc(title)+'</text>';
}
function axisSvg(lx,ty,rx,by) {
    return '<line x1="'+lx+'" y1="'+by+'" x2="'+rx+'" y2="'+by+'" stroke="#CBD5E1" stroke-width="1"/>' +
           '<line x1="'+lx+'" y1="'+ty+'" x2="'+lx+'" y2="'+by+'" stroke="#CBD5E1" stroke-width="1"/>';
}
function gridLines(lx,rx,by,ty,count) {
    var s = ''; for (var i=1;i<=count;i++) { var y=by-(by-ty)*i/count;
        s += '<line x1="'+lx+'" y1="'+y+'" x2="'+rx+'" y2="'+y+'" stroke="#F1F5F9" stroke-width="0.5"/>';
    } return s;
}
function yLabels(lx,by,ty,mn,mx,count) {
    var s = ''; for (var i=0;i<=count;i++) { var y=by-(by-ty)*i/count; var v=mn+(mx-mn)*i/count;
        s += '<text x="'+(lx-5)+'" y="'+(y+4)+'" text-anchor="end" font-size="10" fill="#94A3B8">'+Math.round(v)+'</text>';
    } return s;
}
function bgRect() {
    return '<rect x="0" y="0" width="'+W+'" height="'+H+'" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>';
}
function svgOpen(vw,vh) {
    vw=vw||W; vh=vh||H;
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+vw+' '+vh+'" style="max-width:480px;width:100%;height:auto;">';
}
function allMax(series) { var m=-Infinity; for (var i=0;i<series.length;i++) for (var j=0;j<series[i].values.length;j++) m=Math.max(m,series[i].values[j]); return m; }
function allMin(series) { var m=Infinity; for (var i=0;i<series.length;i++) for (var j=0;j<series[i].values.length;j++) m=Math.min(m,series[i].values[j]); return m; }

function _normalizeConfig(type, config) {
    if (!config || !config.labels || !config.series || !config.series.length) return config;
    var i, si, vals;
    if (type === 'heatmap') {
        var nR = config.labels.length, nC = (config.colLabels || config.labels).length;
        vals = config.series[0].values || (config.series[0].values = []);
        while (vals.length < nR * nC) vals.push(0);
        for (i = 0; i < vals.length; i++) if (vals[i] == null || isNaN(vals[i])) vals[i] = 0;
    } else if (type === 'gauge') {
        vals = config.series[0].values || (config.series[0].values = [0]);
        if (!vals.length) vals.push(0);
        if (vals[0] == null || isNaN(vals[0])) vals[0] = 0;
    } else {
        var n = config.labels.length;
        for (si = 0; si < config.series.length; si++) {
            vals = config.series[si].values;
            if (!vals) { config.series[si].values = []; vals = config.series[si].values; }
            while (vals.length < n) vals.push(0);
            for (i = 0; i < vals.length; i++) if (vals[i] == null || isNaN(vals[i])) vals[i] = 0;
        }
    }
    return config;
}

function legendSvg(series, baseY) {
    var s = '', ns = series.length;
    if (ns === 0) return '';
    var itemW = Math.min(65, (W - PAD.l) / ns);
    var startX = Math.max(PAD.l, W - ns * itemW);
    for (var si = 0; si < ns; si++) {
        var lxp = startX + si * itemW;
        s += '<circle cx="'+lxp+'" cy="'+baseY+'" r="5" fill="'+COLORS[si%COLORS.length]+'"/>';
        s += '<text data-ce="sname:'+si+'" x="'+(lxp+8)+'" y="'+(baseY+4)+'" font-size="10" fill="#334155">'+esc(series[si].name)+'</text>';
    }
    return s;
}

// ── Renderers ──
var R = {};

R.bar = function(c) {
    var labels=c.labels, vals=c.series[0].values, n=labels.length;
    if(n===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var mx=Math.max.apply(null,vals)*1.15||1, lx=PAD.l, rx=W-PAD.r, ty=PAD.t+8, by=H-PAD.b;
    var bw=Math.min(55,(rx-lx)/n*0.6);
    var s=svgOpen()+bgRect()+titleSvg(c.title,250,28)+axisSvg(lx,ty,rx,by)+gridLines(lx,rx,by,ty,3)+yLabels(lx,by,ty,0,mx,3);
    for(var i=0;i<n;i++){
        var x=cx(i,n,lx,rx)-bw/2, v=vals[i], h=(by-ty)*v/mx, y=by-h;
        var cl=COLORS[i%COLORS.length];
        s+='<rect x="'+x+'" y="'+y+'" width="'+bw+'" height="'+h+'" rx="3" fill="'+cl+'"/>';
        s+='<text data-ce="val:0:'+i+'" x="'+(x+bw/2)+'" y="'+(y-5)+'" text-anchor="middle" font-size="11" font-weight="bold" fill="'+cl+'">'+v+'</text>';
        s+='<text data-ce="label:'+i+'" x="'+(x+bw/2)+'" y="'+(by+18)+'" text-anchor="middle" font-size="11" fill="#64748B" font-family="'+FONT+'">'+esc(labels[i])+'</text>';
    }
    return s+'</svg>';
};

R.grouped = function(c) {
    var labels=c.labels, ns=c.series.length, n=labels.length;
    if(n===0||ns===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var mx=allMax(c.series)*1.15||1, lx=PAD.l, rx=W-PAD.r, ty=PAD.t+8, by=H-PAD.b;
    var gw=(rx-lx)/n*0.75, bw=gw/ns;
    var s=svgOpen()+bgRect()+titleSvg(c.title,250,28)+axisSvg(lx,ty,rx,by)+gridLines(lx,rx,by,ty,3);
    for(var i=0;i<n;i++){
        var gx=cx(i,n,lx,rx)-gw/2;
        s+='<text data-ce="label:'+i+'" x="'+cx(i,n,lx,rx)+'" y="'+(by+18)+'" text-anchor="middle" font-size="11" fill="#64748B" font-family="'+FONT+'">'+esc(labels[i])+'</text>';
        for(var si=0;si<ns;si++){
            var v=c.series[si].values[i], h=(by-ty)*v/mx, x=gx+si*bw, y=by-h;
            s+='<rect x="'+x+'" y="'+y+'" width="'+(bw*0.85)+'" height="'+h+'" rx="2" fill="'+COLORS[si%COLORS.length]+'"/>';
        }
    }
    // legend
    s+=legendSvg(c.series, 46);
    return s+'</svg>';
};

R.stacked = function(c) {
    var labels=c.labels, ns=c.series.length, n=labels.length;
    if(n===0||ns===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var totals=[]; for(var i=0;i<n;i++){var t=0;for(var si=0;si<ns;si++)t+=(c.series[si].values[i]||0);totals.push(t);}
    var mx=Math.max.apply(null,totals)*1.1||1, lx=PAD.l, rx=W-PAD.r, ty=PAD.t+8, by=H-PAD.b;
    var bw=Math.min(65,(rx-lx)/n*0.55);
    var s=svgOpen()+bgRect()+titleSvg(c.title,250,28)+axisSvg(lx,ty,rx,by)+gridLines(lx,rx,by,ty,3);
    for(var i=0;i<n;i++){
        var x=cx(i,n,lx,rx)-bw/2, cum=0;
        for(var si=0;si<ns;si++){
            var v=c.series[si].values[i], h=(by-ty)*v/mx, y=by-cum*(by-ty)/mx-h;
            s+='<rect x="'+x+'" y="'+y+'" width="'+bw+'" height="'+h+'" rx="2" fill="'+COLORS[si%COLORS.length]+'"/>';
            cum+=v;
        }
        s+='<text data-ce="label:'+i+'" x="'+(x+bw/2)+'" y="'+(by+18)+'" text-anchor="middle" font-size="12" fill="#64748B" font-family="'+FONT+'">'+esc(labels[i])+'</text>';
    }
    s+=legendSvg(c.series, 46);
    return s+'</svg>';
};

R.h_bar = function(c) {
    var labels=c.labels, vals=c.series[0].values, n=labels.length;
    if(n===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var mx=Math.max.apply(null,vals)*1.15||1, lx=100, rx=W-PAD.r, ty=PAD.t+8;
    var bh=28, gap=8;
    var vh=Math.max(H, ty+n*(bh+gap)+20);
    var by=vh-15;
    var s=svgOpen(W,vh)+'<rect x="0" y="0" width="'+W+'" height="'+vh+'" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>';
    s+=titleSvg(c.title,250,28);
    s+='<line x1="'+lx+'" y1="'+ty+'" x2="'+lx+'" y2="'+by+'" stroke="#CBD5E1" stroke-width="1"/>';
    s+='<line x1="'+lx+'" y1="'+by+'" x2="'+rx+'" y2="'+by+'" stroke="#CBD5E1" stroke-width="1"/>';
    for(var i=0;i<n;i++){
        var y=ty+(by-ty)*(i+0.5)/n-bh/2, w=(rx-lx)*vals[i]/mx, cl=COLORS[i%COLORS.length];
        s+='<text data-ce="label:'+i+'" x="'+(lx-10)+'" y="'+(y+bh/2+4)+'" text-anchor="end" font-size="12" fill="#334155" font-family="'+FONT+'">'+esc(labels[i])+'</text>';
        s+='<rect x="'+lx+'" y="'+y+'" width="'+w+'" height="'+bh+'" rx="3" fill="'+cl+'"/>';
        s+='<text data-ce="val:0:'+i+'" x="'+(lx+w+8)+'" y="'+(y+bh/2+4)+'" font-size="12" font-weight="bold" fill="'+cl+'">'+vals[i]+'</text>';
    }
    return s+'</svg>';
};

R.line = function(c) {
    var labels=c.labels, ns=c.series.length, n=labels.length;
    if(n===0||ns===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var mx=allMax(c.series)*1.15||1, mn=Math.min(0,allMin(c.series));
    var lx=PAD.l, rx=W-PAD.r, ty=PAD.t+8, by=H-PAD.b;
    var s=svgOpen()+bgRect()+titleSvg(c.title,250,28)+axisSvg(lx,ty,rx,by)+gridLines(lx,rx,by,ty,3)+yLabels(lx,by,ty,mn,mx,3);
    for(var si=0;si<ns;si++){
        var pts=[], vals=c.series[si].values, cl=COLORS[si%COLORS.length];
        for(var i=0;i<n;i++){
            var x=cx(i,n,lx,rx), y=lerp(vals[i],mn,mx,by,ty);
            pts.push(x.toFixed(1)+','+y.toFixed(1));
        }
        var dash=si>0?' stroke-dasharray="6,3"':'';
        s+='<polyline points="'+pts.join(' ')+'" fill="none" stroke="'+cl+'" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"'+dash+'/>';
        for(var i=0;i<n;i++){
            var x=cx(i,n,lx,rx), y=lerp(vals[i],mn,mx,by,ty);
            s+='<circle cx="'+x.toFixed(1)+'" cy="'+y.toFixed(1)+'" r="4" fill="#fff" stroke="'+cl+'" stroke-width="2"/>';
        }
    }
    for(var i=0;i<n;i++) s+='<text data-ce="label:'+i+'" x="'+cx(i,n,lx,rx).toFixed(1)+'" y="'+(by+18)+'" text-anchor="middle" font-size="11" fill="#64748B">'+esc(labels[i])+'</text>';
    s+=legendSvg(c.series, 48);
    return s+'</svg>';
};

R.area = function(c) {
    var labels=c.labels, ns=c.series.length, n=labels.length;
    if(n===0||ns===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var mx=allMax(c.series)*1.15||1, mn=Math.min(0,allMin(c.series));
    var lx=PAD.l, rx=W-PAD.r, ty=PAD.t+8, by=H-PAD.b;
    var s=svgOpen()+bgRect()+titleSvg(c.title,250,28)+axisSvg(lx,ty,rx,by)+gridLines(lx,rx,by,ty,3);
    for(var si=0;si<ns;si++){
        var pts=[], vals=c.series[si].values, cl=COLORS[si%COLORS.length];
        for(var i=0;i<n;i++){
            var x=cx(i,n,lx,rx), y=lerp(vals[i],mn,mx,by,ty);
            pts.push(x.toFixed(1)+','+y.toFixed(1));
        }
        var areaPath='M'+pts[0];
        for(var i=1;i<pts.length;i++) areaPath+=' L'+pts[i];
        areaPath+=' L'+cx(n-1,n,lx,rx).toFixed(1)+','+by+' L'+cx(0,n,lx,rx).toFixed(1)+','+by+' Z';
        s+='<path d="'+areaPath+'" fill="'+cl+'" opacity="'+Math.max(0.05,0.25-si*0.05)+'"/>';
        s+='<polyline points="'+pts.join(' ')+'" fill="none" stroke="'+cl+'" stroke-width="2.5" stroke-linecap="round"/>';
    }
    for(var i=0;i<n;i++) s+='<text data-ce="label:'+i+'" x="'+cx(i,n,lx,rx).toFixed(1)+'" y="'+(by+18)+'" text-anchor="middle" font-size="11" fill="#64748B">'+esc(labels[i])+'</text>';
    return s+'</svg>';
};

R.pie = function(c) {
    var labels=c.labels, vals=c.series[0].values, n=labels.length;
    if(n===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var total=0; for(var i=0;i<n;i++) total+=vals[i];
    if(total<=0) total=1;
    var legendH=100+n*30+10;
    var vh=Math.max(H, legendH);
    var cxp=210, cyp=Math.min(165, vh/2+10), r=Math.min(105, (vh-50)/2-10), angle=-Math.PI/2;
    var s=svgOpen(W,vh)+'<rect x="0" y="0" width="'+W+'" height="'+vh+'" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>';
    s+=titleSvg(c.title,250,28);
    for(var i=0;i<n;i++){
        var a=vals[i]/total*2*Math.PI;
        if(a<0.001){angle+=a;continue;}
        var x1=cxp+r*Math.cos(angle), y1=cyp+r*Math.sin(angle);
        angle+=a;
        var x2=cxp+r*Math.cos(angle), y2=cyp+r*Math.sin(angle);
        var large=a>Math.PI?1:0;
        s+='<path d="M'+cxp+','+cyp+' L'+x1.toFixed(1)+','+y1.toFixed(1)+' A'+r+','+r+' 0 '+large+',1 '+x2.toFixed(1)+','+y2.toFixed(1)+' Z" fill="'+COLORS[i%COLORS.length]+'"/>';
    }
    for(var i=0;i<n;i++){
        var pct=total>0?Math.round(vals[i]/total*100):0;
        s+='<circle cx="390" cy="'+(100+i*30)+'" r="6" fill="'+COLORS[i%COLORS.length]+'"/>';
        s+='<text data-ce="label:'+i+'" x="402" y="'+(104+i*30)+'" font-size="12" fill="#334155" font-family="'+FONT+'">'+esc(labels[i])+' '+pct+'%</text>';
    }
    return s+'</svg>';
};

R.donut = function(c) {
    var labels=c.labels, vals=c.series[0].values, n=labels.length;
    if(n===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var total=0; for(var i=0;i<n;i++) total+=vals[i];
    if(total<=0) total=1;
    var legendH=110+n*30+10;
    var vh=Math.max(H, legendH);
    var cxp=210, cyp=Math.min(165, vh/2+10), r=Math.min(105, (vh-50)/2-10), ir=Math.round(r*0.52), angle=-Math.PI/2;
    var s=svgOpen(W,vh)+'<rect x="0" y="0" width="'+W+'" height="'+vh+'" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>';
    s+=titleSvg(c.title,250,28);
    for(var i=0;i<n;i++){
        var a=vals[i]/total*2*Math.PI;
        if(a<0.001){angle+=a;continue;}
        var x1=cxp+r*Math.cos(angle), y1=cyp+r*Math.sin(angle);
        angle+=a;
        var x2=cxp+r*Math.cos(angle), y2=cyp+r*Math.sin(angle);
        var large=a>Math.PI?1:0;
        s+='<path d="M'+cxp+','+cyp+' L'+x1.toFixed(1)+','+y1.toFixed(1)+' A'+r+','+r+' 0 '+large+',1 '+x2.toFixed(1)+','+y2.toFixed(1)+' Z" fill="'+COLORS[i%COLORS.length]+'"/>';
    }
    s+='<circle cx="'+cxp+'" cy="'+cyp+'" r="'+ir+'" fill="#FAFBFC"/>';
    var ct=c.centerText||''; var cl=c.centerLabel||'';
    if(ct) s+='<text data-ce="centerText" x="'+cxp+'" y="'+(cyp-5)+'" text-anchor="middle" font-size="22" font-weight="bold" fill="#1E293B">'+esc(ct)+'</text>';
    if(cl) s+='<text data-ce="centerLabel" x="'+cxp+'" y="'+(cyp+15)+'" text-anchor="middle" font-size="12" fill="#64748B" font-family="'+FONT+'">'+esc(cl)+'</text>';
    for(var i=0;i<n;i++){
        var pct=total>0?Math.round(vals[i]/total*100):0;
        s+='<circle cx="390" cy="'+(110+i*30)+'" r="6" fill="'+COLORS[i%COLORS.length]+'"/>';
        s+='<text data-ce="label:'+i+'" x="402" y="'+(114+i*30)+'" font-size="12" fill="#334155" font-family="'+FONT+'">'+esc(labels[i])+' '+pct+'%</text>';
    }
    return s+'</svg>';
};

R.scatter = function(c) {
    var n=c.labels.length;
    if(n===0||c.series.length<2) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var xVals=c.series[0].values, yVals=c.series[1].values;
    var xMx=Math.max.apply(null,xVals)*1.15||1, yMx=Math.max.apply(null,yVals)*1.15||1;
    var lx=PAD.l, rx=W-PAD.r, ty=PAD.t+8, by=H-PAD.b;
    var s=svgOpen()+bgRect()+titleSvg(c.title,250,28)+axisSvg(lx,ty,rx,by)+gridLines(lx,rx,by,ty,3);
    for(var i=0;i<n;i++){
        var px=lerp(xVals[i],0,xMx,lx,rx), py=lerp(yVals[i],0,yMx,by,ty);
        s+='<circle cx="'+px.toFixed(1)+'" cy="'+py.toFixed(1)+'" r="6" fill="'+COLORS[0]+'" opacity="0.75"/>';
    }
    s+='<text data-ce="xLabel" x="250" y="290" text-anchor="middle" font-size="11" fill="#64748B" font-family="'+FONT+'">'+(c.xLabel||'X')+'</text>';
    s+='<text data-ce="yLabel" x="35" y="155" text-anchor="middle" font-size="11" fill="#64748B" font-family="'+FONT+'" transform="rotate(-90,35,155)">'+(c.yLabel||'Y')+'</text>';
    return s+'</svg>';
};

R.bubble = function(c) {
    var n=c.labels.length;
    if(n===0||c.series.length<2) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var vals=c.series[0].values, sizes=c.series[1].values;
    var mx=Math.max.apply(null,vals)*1.15||1, smx=Math.max.apply(null,sizes)||1;
    var lx=PAD.l, rx=W-PAD.r, ty=PAD.t+8, by=H-PAD.b;
    var s=svgOpen()+bgRect()+titleSvg(c.title,250,28)+axisSvg(lx,ty,rx,by);
    for(var i=0;i<n;i++){
        var px=lx+(rx-lx)*(i+1)/(n+1), py=lerp(vals[i],0,mx,by,ty);
        var r=Math.max(10,sizes[i]/smx*45);
        s+='<circle cx="'+px.toFixed(1)+'" cy="'+py.toFixed(1)+'" r="'+r.toFixed(1)+'" fill="'+COLORS[i%COLORS.length]+'" opacity="0.5"/>';
    }
    s+='<text data-ce="xLabel" x="250" y="290" text-anchor="middle" font-size="11" fill="#64748B" font-family="'+FONT+'">'+(c.xLabel||'X')+'</text>';
    s+='<text data-ce="yLabel" x="35" y="155" text-anchor="middle" font-size="11" fill="#64748B" font-family="'+FONT+'" transform="rotate(-90,35,155)">'+(c.yLabel||'Y')+'</text>';
    return s+'</svg>';
};

R.radar = function(c) {
    var labels=c.labels, vals=c.series[0].values, n=labels.length;
    if(n<3) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var cxp=250, cyp=170, r=100;
    var mx=Math.max.apply(null,vals)*1.1||1;
    var s=svgOpen()+bgRect()+titleSvg(c.title,250,28);
    // axes + outline
    var outline=[]; for(var i=0;i<n;i++){
        var a=-Math.PI/2+i*2*Math.PI/n;
        var px=cxp+r*Math.cos(a), py=cyp+r*Math.sin(a);
        outline.push(px.toFixed(1)+','+py.toFixed(1));
        s+='<line x1="'+cxp+'" y1="'+cyp+'" x2="'+px.toFixed(1)+'" y2="'+py.toFixed(1)+'" stroke="#CBD5E1" stroke-width="0.8"/>';
        var lx2=cxp+(r+18)*Math.cos(a), ly2=cyp+(r+18)*Math.sin(a);
        s+='<text data-ce="label:'+i+'" x="'+lx2.toFixed(1)+'" y="'+ly2.toFixed(1)+'" text-anchor="middle" font-size="12" fill="#334155" font-family="'+FONT+'">'+esc(labels[i])+'</text>';
    }
    s+='<polygon points="'+outline.join(' ')+'" fill="none" stroke="#CBD5E1" stroke-width="1"/>';
    // data
    var dpts=[]; for(var i=0;i<n;i++){
        var a=-Math.PI/2+i*2*Math.PI/n, ratio=vals[i]/mx;
        dpts.push((cxp+r*ratio*Math.cos(a)).toFixed(1)+','+(cyp+r*ratio*Math.sin(a)).toFixed(1));
    }
    s+='<polygon points="'+dpts.join(' ')+'" fill="'+COLORS[0]+'" fill-opacity="0.3" stroke="'+COLORS[0]+'" stroke-width="2.5"/>';
    return s+'</svg>';
};

R.funnel = function(c) {
    var labels=c.labels, vals=c.series[0].values, n=labels.length;
    if(n===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var mx=Math.max.apply(null,vals)||1;
    var sh=50, gap=5, eh=Math.max(20,(H-sh-20)/n);
    var vh=Math.max(H, sh+n*(eh+gap)+10);
    var s=svgOpen(W,vh)+'<rect x="0" y="0" width="'+W+'" height="'+vh+'" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>';
    s+=titleSvg(c.title,250,28);
    for(var i=0;i<n;i++){
        var w1=(i===0?1:vals[i-1]/mx)*400, w2=vals[i]/mx*400;
        if(i===0) w1=400;
        var y=sh+i*(eh+gap), x1l=250-w1/2, x1r=250+w1/2, x2l=250-w2/2, x2r=250+w2/2;
        s+='<polygon points="'+x1l+','+y+' '+x1r+','+y+' '+x2r+','+(y+eh)+' '+x2l+','+(y+eh)+'" fill="'+COLORS[i%COLORS.length]+'"/>';
        s+='<text data-ce="label:'+i+'" x="250" y="'+(y+eh*0.65)+'" text-anchor="middle" font-size="13" fill="white" font-weight="bold">'+esc(labels[i])+' '+vals[i]+'</text>';
    }
    return s+'</svg>';
};

R.gauge = function(c) {
    var val=c.series[0].values[0], mx=c.max||100, unit=c.unit||'%';
    if(mx<=0) mx=100;
    var label=c.labels[0]||'';
    var pct=Math.min(val/mx,1);
    // Semi-circle gauge
    var s=svgOpen()+bgRect()+titleSvg(c.title,250,28);
    var cxp=250, cyp=230, gr=150;
    // bg arc (full semi)
    s+='<path d="M'+(cxp-gr)+','+cyp+' A'+gr+','+gr+' 0 0,1 '+(cxp+gr)+','+cyp+'" fill="none" stroke="#E2E8F0" stroke-width="28" stroke-linecap="round"/>';
    // value arc
    var endAngle=Math.PI*(1-pct);
    var ex=cxp+gr*Math.cos(endAngle), ey=cyp-gr*Math.sin(endAngle);
    var large=pct>0.5?1:0;
    s+='<path d="M'+(cxp-gr)+','+cyp+' A'+gr+','+gr+' 0 '+large+',1 '+ex.toFixed(1)+','+ey.toFixed(1)+'" fill="none" stroke="'+COLORS[0]+'" stroke-width="28" stroke-linecap="round"/>';
    s+='<text data-ce="val:0:0" x="'+cxp+'" y="200" text-anchor="middle" font-size="48" font-weight="bold" fill="#1E293B">'+val+'</text>';
    s+='<text data-ce="label:0" x="'+cxp+'" y="230" text-anchor="middle" font-size="16" fill="#64748B" font-family="'+FONT+'">'+esc(label)+' '+esc(unit)+'</text>';
    s+='<text x="'+(cxp-gr+10)+'" y="260" text-anchor="middle" font-size="11" fill="#94A3B8">0</text>';
    s+='<text x="'+cxp+'" y="80" text-anchor="middle" font-size="11" fill="#94A3B8">'+Math.round(mx/2)+'</text>';
    s+='<text x="'+(cxp+gr-10)+'" y="260" text-anchor="middle" font-size="11" fill="#94A3B8">'+mx+'</text>';
    return s+'</svg>';
};

R.waterfall = function(c) {
    var labels=c.labels, vals=c.series[0].values, n=labels.length;
    if(n===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var lx=PAD.l, rx=W-PAD.r, ty=PAD.t+8, by=H-PAD.b;
    // compute cumulative
    var cum=[vals[0]], runVal=vals[0]; for(var i=1;i<n;i++){runVal+=vals[i];cum.push(runVal);}
    var allVals=[]; for(var i=0;i<n;i++){allVals.push(cum[i]);if(i>0)allVals.push(cum[i]-vals[i]);}
    var mx=Math.max.apply(null,allVals)*1.15||1, mn=Math.min(0,Math.min.apply(null,allVals))*1.1;
    var bw=Math.min(50,(rx-lx)/n*0.55);
    var s=svgOpen()+bgRect()+titleSvg(c.title,250,28)+axisSvg(lx,ty,rx,by)+gridLines(lx,rx,by,ty,3);
    for(var i=0;i<n;i++){
        var x=cx(i,n,lx,rx)-bw/2, base=i===0?0:cum[i-1], top=cum[i];
        var y1=lerp(Math.max(base,top),mn,mx,by,ty), y2=lerp(Math.min(base,top),mn,mx,by,ty);
        var cl=i===0||i===n-1?COLORS[4]:(vals[i]>=0?COLORS[1]:COLORS[3]);
        s+='<rect x="'+x+'" y="'+y1+'" width="'+bw+'" height="'+(y2-y1||1)+'" rx="2" fill="'+cl+'"/>';
        var txt=i===0?vals[0]:(vals[i]>=0?'+'+vals[i]:vals[i]);
        s+='<text data-ce="val:0:'+i+'" x="'+(x+bw/2)+'" y="'+(y1-5)+'" text-anchor="middle" font-size="11" font-weight="bold" fill="'+cl+'">'+txt+'</text>';
        s+='<text data-ce="label:'+i+'" x="'+(x+bw/2)+'" y="'+(by+18)+'" text-anchor="middle" font-size="10" fill="#64748B">'+esc(labels[i])+'</text>';
        // connector line
        if(i<n-1){
            var nx=cx(i+1,n,lx,rx)-bw/2;
            var cy2=lerp(cum[i],mn,mx,by,ty);
            s+='<line x1="'+(x+bw)+'" y1="'+cy2+'" x2="'+nx+'" y2="'+cy2+'" stroke="#94A3B8" stroke-width="1" stroke-dasharray="3,2"/>';
        }
    }
    return s+'</svg>';
};

R.progress = function(c) {
    var labels=c.labels, vals=c.series[0].values, n=labels.length;
    if(n===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var vh=50+n*40; var bw=300, bx=130;
    var s=svgOpen(W,vh)+'<rect x="0" y="0" width="'+W+'" height="'+vh+'" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>';
    s+=titleSvg(c.title,250,28);
    for(var i=0;i<n;i++){
        var y=50+i*40, v=Math.min(vals[i],100), cl=COLORS[i%COLORS.length];
        s+='<text data-ce="label:'+i+'" x="60" y="'+(y+12)+'" font-size="12" fill="#334155" font-family="'+FONT+'">'+esc(labels[i])+'</text>';
        s+='<rect x="'+bx+'" y="'+y+'" width="'+bw+'" height="18" rx="9" fill="#E2E8F0"/>';
        s+='<rect x="'+bx+'" y="'+y+'" width="'+(bw*v/100)+'" height="18" rx="9" fill="'+cl+'"/>';
        s+='<text data-ce="val:0:'+i+'" x="'+(bx+bw+15)+'" y="'+(y+13)+'" font-size="12" font-weight="bold" fill="'+cl+'">'+v+'%</text>';
    }
    return s+'</svg>';
};

R.heatmap = function(c) {
    var rowLabels=c.labels, colLabels=c.colLabels||c.labels;
    var vals=c.series[0].values, nR=rowLabels.length, nC=colLabels.length;
    if(nR===0||nC===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var cw=64, ch=38, ox=110, oy=58;
    var vw=Math.max(W, ox+nC*cw+20), vh=Math.max(H, oy+nR*ch+20);
    var mn=Infinity, mx=-Infinity;
    for(var i=0;i<vals.length;i++){mn=Math.min(mn,vals[i]);mx=Math.max(mx,vals[i]);}
    var s=svgOpen(vw,vh)+'<rect x=\"0\" y=\"0\" width=\"'+vw+'\" height=\"'+vh+'\" rx=\"8\" fill=\"#FAFBFC\" stroke=\"#E2E8F0\" stroke-width=\"1\"/>'+titleSvg(c.title,250,28);
    for(var ci=0;ci<nC;ci++) s+='<text data-ce="col:'+ci+'" x="'+(ox+ci*cw+cw/2)+'" y="52" text-anchor="middle" font-size="11" fill="#334155" font-family="'+FONT+'">'+esc(colLabels[ci])+'</text>';
    for(var ri=0;ri<nR;ri++){
        s+='<text data-ce="label:'+ri+'" x="'+(ox-10)+'" y="'+(oy+ri*ch+ch/2+4)+'" text-anchor="end" font-size="11" fill="#334155" font-family="'+FONT+'">'+esc(rowLabels[ri])+'</text>';
        for(var ci=0;ci<nC;ci++){
            var idx=ri*nC+ci, v=vals[idx]||0;
            var t=(v-mn)/(mx-mn||1);
            var r2=Math.round(219-186*t), g2=Math.round(234-156*t), b2=Math.round(254-19*t);
            var fill='rgb('+r2+','+g2+','+b2+')';
            var tx=t>0.6?'#fff':'#1E293B';
            var x=ox+ci*cw, y=oy+ri*ch;
            s+='<rect x="'+x+'" y="'+y+'" width="'+cw+'" height="'+ch+'" rx="4" fill="'+fill+'"/>';
            s+='<text data-ce="val:0:'+(ri*nC+ci)+'" x="'+(x+cw/2)+'" y="'+(y+ch/2+4)+'" text-anchor="middle" font-size="12" fill="'+tx+'">'+v+'</text>';
        }
    }
    return s+'</svg>';
};

R.gantt = function(c) {
    if(c.series.length<2) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'<text x=\"250\" y=\"150\" text-anchor=\"middle\" font-size=\"14\" fill=\"#94A3B8\">需要2组数据</text></svg>';
    var labels=c.labels, starts=c.series[0].values, durations=c.series[1].values, n=labels.length;
    if(n===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var totalEnd=0; for(var i=0;i<n;i++) totalEnd=Math.max(totalEnd,starts[i]+durations[i]);
    totalEnd=totalEnd*1.1||1;
    var vh=Math.max(280,60+n*40+20);
    var lx=120, rx=W-30, ty=60, by=ty+n*40;
    var s=svgOpen(W,vh)+'<rect x="0" y="0" width="'+W+'" height="'+vh+'" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>';
    s+=titleSvg(c.title,250,28);
    // time grid
    var ticks=Math.min(6,Math.ceil(totalEnd)); for(var t=0;t<=ticks;t++){
        var x=lx+(rx-lx)*t/ticks;
        s+='<line x1="'+x+'" y1="'+ty+'" x2="'+x+'" y2="'+by+'" stroke="#E2E8F0" stroke-width="0.5"/>';
        s+='<text x="'+x+'" y="'+(ty-8)+'" text-anchor="middle" font-size="10" fill="#94A3B8">'+(Math.round(t*totalEnd/ticks*10)/10)+'</text>';
    }
    for(var i=0;i<n;i++){
        var y=ty+i*40+8, bh=22;
        s+='<text data-ce="label:'+i+'" x="'+(lx-10)+'" y="'+(y+bh/2+4)+'" text-anchor="end" font-size="12" fill="#334155" font-family="'+FONT+'">'+esc(labels[i])+'</text>';
        var x=lx+(rx-lx)*starts[i]/totalEnd, w=Math.max(10,(rx-lx)*durations[i]/totalEnd);
        s+='<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+bh+'" rx="11" fill="'+COLORS[i%COLORS.length]+'"/>';
    }
    return s+'</svg>';
};

R.boxplot = function(c) {
    if(c.series.length<5) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'<text x=\"250\" y=\"150\" text-anchor=\"middle\" font-size=\"14\" fill=\"#94A3B8\">需要5组数据(min,Q1,中位数,Q3,max)</text></svg>';
    var labels=c.labels, n=labels.length;
    if(n===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var mins=c.series[0].values,q1s=c.series[1].values,meds=c.series[2].values,q3s=c.series[3].values,maxs=c.series[4].values;
    var allMn=Math.min.apply(null,mins)*0.9, allMx=Math.max.apply(null,maxs)*1.1;
    if(allMx===allMn){allMx=allMn+1;}
    var lx=PAD.l, rx=W-PAD.r, ty=PAD.t+8, by=H-PAD.b;
    var bw=Math.min(60,(rx-lx)/n*0.5);
    var s=svgOpen()+bgRect()+titleSvg(c.title,250,28)+axisSvg(lx,ty,rx,by)+gridLines(lx,rx,by,ty,3);
    for(var i=0;i<n;i++){
        var xc=cx(i,n,lx,rx), cl=COLORS[i%COLORS.length];
        var yMin=lerp(mins[i],allMn,allMx,by,ty), yQ1=lerp(q1s[i],allMn,allMx,by,ty);
        var yMed=lerp(meds[i],allMn,allMx,by,ty), yQ3=lerp(q3s[i],allMn,allMx,by,ty);
        var yMax=lerp(maxs[i],allMn,allMx,by,ty);
        // whiskers
        s+='<line x1="'+xc+'" y1="'+yMax+'" x2="'+xc+'" y2="'+yQ3+'" stroke="'+cl+'" stroke-width="2"/>';
        s+='<line x1="'+xc+'" y1="'+yQ1+'" x2="'+xc+'" y2="'+yMin+'" stroke="'+cl+'" stroke-width="2"/>';
        s+='<line x1="'+(xc-bw*0.3)+'" y1="'+yMax+'" x2="'+(xc+bw*0.3)+'" y2="'+yMax+'" stroke="'+cl+'" stroke-width="2"/>';
        s+='<line x1="'+(xc-bw*0.3)+'" y1="'+yMin+'" x2="'+(xc+bw*0.3)+'" y2="'+yMin+'" stroke="'+cl+'" stroke-width="2"/>';
        // box
        s+='<rect x="'+(xc-bw/2)+'" y="'+yQ3+'" width="'+bw+'" height="'+(yQ1-yQ3)+'" rx="4" fill="'+cl+'" opacity="0.2" stroke="'+cl+'" stroke-width="2"/>';
        s+='<line x1="'+(xc-bw/2)+'" y1="'+yMed+'" x2="'+(xc+bw/2)+'" y2="'+yMed+'" stroke="'+cl+'" stroke-width="3"/>';
        s+='<text data-ce="label:'+i+'" x="'+xc+'" y="'+(by+18)+'" text-anchor="middle" font-size="12" fill="#64748B" font-family="'+FONT+'">'+esc(labels[i])+'</text>';
    }
    return s+'</svg>';
};

R.dual_axis = function(c) {
    if(c.series.length<2) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'<text x=\"250\" y=\"150\" text-anchor=\"middle\" font-size=\"14\" fill=\"#94A3B8\">需要2组数据</text></svg>';
    var labels=c.labels, n=labels.length;
    if(n===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var barVals=c.series[0].values, lineVals=c.series[1].values;
    var bMx=Math.max.apply(null,barVals)*1.15||1, lMx=Math.max.apply(null,lineVals)*1.15||1;
    var lx=65, rx=435, ty=PAD.t+8, by=H-PAD.b;
    var bw=Math.min(50,(rx-lx)/n*0.45);
    var s=svgOpen()+bgRect()+titleSvg(c.title,250,28);
    s+='<line x1="'+lx+'" y1="'+by+'" x2="'+rx+'" y2="'+by+'" stroke="#CBD5E1" stroke-width="1"/>';
    s+='<line x1="'+lx+'" y1="'+ty+'" x2="'+lx+'" y2="'+by+'" stroke="'+COLORS[0]+'" stroke-width="1"/>';
    s+='<line x1="'+rx+'" y1="'+ty+'" x2="'+rx+'" y2="'+by+'" stroke="'+COLORS[3]+'" stroke-width="1"/>';
    // bars
    for(var i=0;i<n;i++){
        var x=cx(i,n,lx,rx)-bw/2, v=barVals[i], h=(by-ty)*v/bMx;
        s+='<rect x="'+x+'" y="'+(by-h)+'" width="'+bw+'" height="'+h+'" rx="3" fill="'+COLORS[0]+'" opacity="0.55"/>';
        s+='<text data-ce="label:'+i+'" x="'+cx(i,n,lx,rx)+'" y="'+(by+18)+'" text-anchor="middle" font-size="11" fill="#64748B">'+esc(labels[i])+'</text>';
    }
    // line
    var pts=[];
    for(var i=0;i<n;i++){
        var x=cx(i,n,lx,rx), y=lerp(lineVals[i],0,lMx,by,ty);
        pts.push(x.toFixed(1)+','+y.toFixed(1));
    }
    s+='<polyline points="'+pts.join(' ')+'" fill="none" stroke="'+COLORS[3]+'" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>';
    for(var i=0;i<n;i++){
        var x=cx(i,n,lx,rx), y=lerp(lineVals[i],0,lMx,by,ty);
        s+='<circle cx="'+x.toFixed(1)+'" cy="'+y.toFixed(1)+'" r="5" fill="#fff" stroke="'+COLORS[3]+'" stroke-width="2.5"/>';
    }
    // legend
    s+='<rect x="140" y="42" width="10" height="10" rx="2" fill="'+COLORS[0]+'" opacity="0.55"/><text data-ce="sname:0" x="155" y="51" font-size="10" fill="#334155">'+esc(c.series[0].name)+'</text>';
    s+='<line x1="220" y1="47" x2="240" y2="47" stroke="'+COLORS[3]+'" stroke-width="2.5"/><text data-ce="sname:1" x="245" y="51" font-size="10" fill="#334155">'+esc(c.series[1].name)+'</text>';
    return s+'</svg>';
};

R.diverging = function(c) {
    if(c.series.length<2) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'<text x=\"250\" y=\"150\" text-anchor=\"middle\" font-size=\"14\" fill=\"#94A3B8\">需要2组数据</text></svg>';
    var labels=c.labels, n=labels.length;
    if(n===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var leftVals=c.series[0].values, rightVals=c.series[1].values;
    var mx=0; for(var i=0;i<n;i++) mx=Math.max(mx,leftVals[i],rightVals[i]);
    mx=mx*1.15||1; var mid=250, hw=180, bh=26, gap=50;
    var vh=Math.max(H, 62+n*gap+bh+30);
    var s=svgOpen(W,vh)+'<rect x=\"0\" y=\"0\" width=\"'+W+'\" height=\"'+vh+'\" rx=\"8\" fill=\"#FAFBFC\" stroke=\"#E2E8F0\" stroke-width=\"1\"/>'+titleSvg(c.title,250,28);
    var lineBottom=62+(n-1)*gap+bh;
    s+='<line x1="'+mid+'" y1="45" x2="'+mid+'" y2="'+lineBottom+'" stroke="#CBD5E1" stroke-width="1"/>';
    for(var i=0;i<n;i++){
        var y=62+i*gap;
        var lw=hw*leftVals[i]/mx, rw=hw*rightVals[i]/mx;
        s+='<text data-ce="label:'+i+'" x="58" y="'+(y+bh/2+4)+'" text-anchor="end" font-size="12" fill="#334155" font-family="'+FONT+'">'+esc(labels[i])+'</text>';
        s+='<rect x="'+(mid-lw)+'" y="'+y+'" width="'+lw+'" height="'+bh+'" rx="4" fill="'+COLORS[3]+'" opacity="0.8"/>';
        s+='<text data-ce="val:0:'+i+'" x="'+(mid-lw/2)+'" y="'+(y+bh/2+4)+'" text-anchor="middle" font-size="11" fill="white" font-weight="bold">'+leftVals[i]+'%</text>';
        s+='<rect x="'+mid+'" y="'+y+'" width="'+rw+'" height="'+bh+'" rx="4" fill="'+COLORS[0]+'" opacity="0.8"/>';
        s+='<text data-ce="val:1:'+i+'" x="'+(mid+rw/2)+'" y="'+(y+bh/2+4)+'" text-anchor="middle" font-size="11" fill="white" font-weight="bold">'+rightVals[i]+'%</text>';
    }
    var legendY=62+(n-1)*gap+bh+25;
    s+='<text x="130" y="'+legendY+'" text-anchor="middle" font-size="10" fill="'+COLORS[3]+'">← '+esc(c.series[0].name)+'</text>';
    s+='<text x="370" y="'+legendY+'" text-anchor="middle" font-size="10" fill="'+COLORS[0]+'">'+esc(c.series[1].name)+' →</text>';
    return s+'</svg>';
};

R.treemap = function(c) {
    var labels=c.labels, vals=c.series[0].values, n=labels.length;
    if(n===0) return svgOpen()+bgRect()+titleSvg(c.title,250,28)+'</svg>';
    var total=0; for(var i=0;i<n;i++) total+=vals[i];
    if(total<=0) total=1;
    // Simple treemap layout: first item gets left half, rest in right
    var s=svgOpen()+bgRect()+titleSvg(c.title,250,28);
    var padX=15, padY=42, aW=W-2*padX, aH=H-padY-10;
    // Squarified approximation: lay out in rows
    var rects=[], areas=[]; for(var i=0;i<n;i++) areas.push(vals[i]/total*aW*aH);
    var x=padX, y=padY, remW=aW, remH=aH;
    // Simple slice layout (alternating horizontal/vertical)
    var remTotal=total;
    var horiz=true;
    var items=[]; for(var i=0;i<n;i++) items.push({label:labels[i],val:vals[i],pct:Math.round(vals[i]/total*100)});
    // Use slice-and-dice
    function layout(its, x, y, w, h, hz) {
        if(its.length===0) return;
        if(its.length===1){rects.push({x:x,y:y,w:w,h:h,label:its[0].label,pct:its[0].pct});return;}
        var tot=0; for(var i=0;i<its.length;i++) tot+=its[i].val;
        var half=tot/2, cum=0, split=0;
        for(var i=0;i<its.length-1;i++){cum+=its[i].val;if(cum>=half){split=i+1;break;}}
        if(split===0) split=1;
        var r1=0; for(var i=0;i<split;i++) r1+=its[i].val;
        var ratio=tot>0?r1/tot:split/its.length;
        if(hz){
            layout(its.slice(0,split),x,y,w*ratio,h,!hz);
            layout(its.slice(split),x+w*ratio,y,w*(1-ratio),h,!hz);
        } else {
            layout(its.slice(0,split),x,y,w,h*ratio,!hz);
            layout(its.slice(split),x,y+h*ratio,w,h*(1-ratio),!hz);
        }
    }
    layout(items,padX,padY,aW,aH,true);
    for(var i=0;i<rects.length;i++){
        var rc=rects[i], cl=COLORS[i%COLORS.length];
        s+='<rect x="'+rc.x.toFixed(1)+'" y="'+rc.y.toFixed(1)+'" width="'+rc.w.toFixed(1)+'" height="'+rc.h.toFixed(1)+'" rx="6" fill="'+cl+'"/>';
        if(rc.w>40&&rc.h>30){
            var fs=Math.min(16,rc.w/6);
        s+='<text data-ce="label:'+i+'" x="'+(rc.x+rc.w/2).toFixed(1)+'" y="'+(rc.y+rc.h/2-2).toFixed(1)+'" text-anchor="middle" font-size="'+fs+'" font-weight="bold" fill="white">'+esc(rc.label)+'</text>';
            s+='<text data-ce="val:0:'+i+'" x="'+(rc.x+rc.w/2).toFixed(1)+'" y="'+(rc.y+rc.h/2+14).toFixed(1)+'" text-anchor="middle" font-size="'+(fs*0.75)+'" fill="rgba(255,255,255,0.8)">'+rc.pct+'%</text>';
        }
    }
    return s+'</svg>';
};

// ── Chart edit modal ──

var _editModal = null;
var _editTarget = null;
var _editType = null;
var _editConfig = null;
var _livePreviewTimer = null;

function _createModal() {
    var overlay = document.createElement('div');
    overlay.id = 'chart-edit-overlay';
    overlay.innerHTML = [
        '<div id="chart-edit-modal">',
        '  <div class="cem-header">',
        '    <span class="cem-title">✎ 编辑图表数据</span>',
        '    <span class="cem-close" id="cem-close">×</span>',
        '  </div>',
        '  <div class="cem-body">',
        '    <div class="cem-row"><label>标题</label><input type="text" id="cem-chart-title" /></div>',
        '    <div class="cem-row" id="cem-extra-fields"></div>',
        '    <div class="cem-section-title">数据表格 <span style="color:#94A3B8;font-size:12px">(直接点击单元格编辑，修改后实时预览)</span></div>',
        '    <div class="cem-table-wrap" id="cem-table-wrap"></div>',
        '    <div class="cem-row-actions">',
        '      <button id="cem-add-col" class="cem-btn-sm">+ 添加列</button>',
        '      <button id="cem-add-row" class="cem-btn-sm">+ 添加行</button>',
        '      <button id="cem-del-col" class="cem-btn-sm cem-btn-danger">- 删除列</button>',
        '      <button id="cem-del-row" class="cem-btn-sm cem-btn-danger">- 删除行</button>',
        '    </div>',
        '    <div class="cem-section-title">实时预览</div>',
        '    <div id="cem-live-preview" style="text-align:center;padding:8px 0;min-height:100px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;margin-top:6px;"></div>',
        '  </div>',
        '  <div class="cem-footer">',
        '    <button id="cem-cancel" class="cem-btn">取消</button>',
        '    <button id="cem-save" class="cem-btn cem-btn-primary">应用</button>',
        '  </div>',
        '</div>'
    ].join('\n');
    document.body.appendChild(overlay);

    // Style
    var style = document.createElement('style');
    style.textContent = [
        '#chart-edit-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.35);z-index:10000;display:flex;align-items:center;justify-content:center;}',
        '#chart-edit-modal{background:#fff;border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,0.18);width:580px;max-width:95vw;max-height:85vh;display:flex;flex-direction:column;font-family:"Microsoft YaHei",sans-serif;}',
        '.cem-header{display:flex;justify-content:space-between;align-items:center;padding:14px 20px;border-bottom:1px solid #e2e8f0;}',
        '.cem-title{font-size:16px;font-weight:bold;color:#1e293b;}',
        '.cem-close{cursor:pointer;font-size:22px;color:#94a3b8;line-height:1;}',
        '.cem-close:hover{color:#e74c3c;}',
        '.cem-body{padding:16px 20px;overflow-y:auto;flex:1;}',
        '.cem-row{margin-bottom:10px;}',
        '.cem-row label{display:block;font-size:13px;color:#475569;margin-bottom:4px;}',
        '.cem-row input[type=text]{width:100%;box-sizing:border-box;padding:7px 10px;border:1px solid #cbd5e1;border-radius:6px;font-size:14px;outline:none;}',
        '.cem-row input[type=text]:focus{border-color:#4a90d9;box-shadow:0 0 0 2px rgba(74,144,217,0.15);}',
        '.cem-section-title{font-size:13px;font-weight:bold;color:#334155;margin:12px 0 6px;}',
        '.cem-table-wrap{overflow-x:auto;margin-bottom:8px;}',
        '.cem-table-wrap table{border-collapse:collapse;width:100%;font-size:13px;}',
        '.cem-table-wrap th,.cem-table-wrap td{border:1px solid #e2e8f0;padding:0;text-align:center;min-width:60px;}',
        '.cem-table-wrap th{background:#f1f5f9;color:#334155;font-weight:600;}',
        '.cem-table-wrap td{cursor:text;}',
        '.cem-table-wrap td input,.cem-table-wrap th input{display:block;width:100%;box-sizing:border-box;border:none;background:transparent;text-align:center;font-size:13px;padding:6px 8px;outline:none;font-family:"Microsoft YaHei",sans-serif;color:#334155;min-height:30px;}',
        '.cem-table-wrap th input{font-weight:600;background:#f1f5f9;}',
        '.cem-table-wrap input:focus{outline:2px solid #4a90d9;background:#eff6ff;border-radius:2px;}',
        '.cem-row-actions{display:flex;gap:8px;margin-bottom:8px;}',
        '.cem-btn-sm{padding:4px 10px;font-size:12px;border:1px solid #cbd5e1;border-radius:5px;background:#fff;cursor:pointer;color:#475569;}',
        '.cem-btn-sm:hover{background:#f1f5f9;}',
        '.cem-btn-danger{color:#d9534f;border-color:#f5c6cb;}',
        '.cem-btn-danger:hover{background:#fdecea!important;}',
        '.cem-footer{display:flex;justify-content:flex-end;gap:8px;padding:12px 20px;border-top:1px solid #e2e8f0;}',
        '.cem-btn{padding:8px 20px;border-radius:8px;font-size:14px;cursor:pointer;border:1px solid #cbd5e1;background:#fff;color:#475569;}',
        '.cem-btn:hover{background:#f1f5f9;}',
        '.cem-btn-primary{background:#4a90d9;color:#fff;border:none;}',
        '.cem-btn-primary:hover{background:#3a7bc8;}'
    ].join('\n');
    document.head.appendChild(style);

    document.getElementById('cem-close').onclick = _closeModal;
    document.getElementById('cem-cancel').onclick = _closeModal;
    document.getElementById('cem-save').onclick = _saveChart;
    document.getElementById('cem-add-col').onclick = function() { _modTable('addCol'); _scheduleLivePreview(); };
    document.getElementById('cem-add-row').onclick = function() { _modTable('addRow'); _scheduleLivePreview(); };
    document.getElementById('cem-del-col').onclick = function() { _modTable('delCol'); _scheduleLivePreview(); };
    document.getElementById('cem-del-row').onclick = function() { _modTable('delRow'); _scheduleLivePreview(); };
    overlay.addEventListener('mousedown', function(e) { if (e.target === overlay) _closeModal(); });

    // 监听表格编辑，实时更新预览
    var tableWrap = document.getElementById('cem-table-wrap');
    tableWrap.addEventListener('input', function() { _scheduleLivePreview(); });
    // 监听标题输入
    document.getElementById('cem-chart-title').addEventListener('input', function() { _scheduleLivePreview(); });

    _editModal = overlay;
}

function _scheduleLivePreview() {
    if (_livePreviewTimer) clearTimeout(_livePreviewTimer);
    _livePreviewTimer = setTimeout(_updateLivePreview, 200);
}

function _updateLivePreview() {
    if (!_editType || !_editConfig) return;
    var renderer = R[_editType];
    if (!renderer) return;
    try {
        var newCfg = _readTable(_editType, _editConfig);
        // 读取额外字段
        if (_editType === 'donut') {
            var ctEl = document.getElementById('cem-center-text');
            var clEl = document.getElementById('cem-center-label');
            if (ctEl) newCfg.centerText = ctEl.value;
            if (clEl) newCfg.centerLabel = clEl.value;
        }
        _normalizeConfig(_editType, newCfg);
        var svgHtml = renderer(newCfg);
        var previewEl = document.getElementById('cem-live-preview');
        if (previewEl) previewEl.innerHTML = svgHtml;
    } catch(e) {
        console.warn('Live preview error:', e);
    }
}

function _closeModal() {
    if (_editModal) _editModal.style.display = 'none';
    _editTarget = null;
}

function _modTable(action) {
    var tbl = document.querySelector('#cem-table-wrap table');
    if (!tbl) return;
    var type = _editType;
    var shape = type ? _getTableShape(type) : 'labels_only';
    var fixedSeries = {boxplot:1,dual_axis:1,gantt:1,scatter:1,bubble:1,diverging:1};
    function _mkInp(val) {
        return '<input type="text" value="' + String(val).replace(/&/g,'&amp;').replace(/"/g,'&quot;') + '">';
    }
    if (action === 'addCol') {
        if (shape === 'gauge_1') return;
        for (var i = 0; i < tbl.rows.length; i++) {
            var cell = i === 0 ? document.createElement('th') : document.createElement('td');
            cell.innerHTML = _mkInp(i === 0 ? '新列' : '0');
            tbl.rows[i].appendChild(cell);
        }
    } else if (action === 'addRow') {
        if (shape === 'gauge_1' || shape === 'labels_only' || shape === 'donut_center') return;
        if (type && fixedSeries[type]) return;
        var tr = document.createElement('tr');
        var cols = tbl.rows[0] ? tbl.rows[0].cells.length : 1;
        for (var j = 0; j < cols; j++) {
            var td = document.createElement('td');
            td.innerHTML = _mkInp(j === 0 ? '新行' : '0');
            tr.appendChild(td);
        }
        tbl.appendChild(tr);
    } else if (action === 'delCol') {
        if (shape === 'gauge_1') return;
        if (tbl.rows[0] && tbl.rows[0].cells.length > 2) {
            for (var i = 0; i < tbl.rows.length; i++) {
                tbl.rows[i].deleteCell(tbl.rows[i].cells.length - 1);
            }
        }
    } else if (action === 'delRow') {
        if (shape === 'gauge_1' || shape === 'labels_only' || shape === 'donut_center') return;
        if (type && fixedSeries[type]) return;
        if (tbl.rows.length > 2) {
            tbl.deleteRow(tbl.rows.length - 1);
        }
    }
}

// Determine table shape based on chart type
function _getTableShape(type) {
    // 'labels_only': labels + single series values (bar, h_bar, pie, funnel, progress, radar, treemap)
    // 'multi_series': labels row + multiple series rows (grouped, stacked, line, area, dual_axis)
    // 'xy': labels as point names, 2 series (x, y) (scatter)
    // 'bubble_xy': labels, values, sizes (bubble)
    // 'boxplot_5': labels, 5 stat series (min,q1,median,q3,max)
    // 'heatmap_grid': row labels × col labels → flat values
    // 'gantt_2': labels, start, duration
    // 'waterfall_1': labels, values (allow negative)
    // 'gauge_1': single value
    // 'donut_center': pie + centerText/centerLabel
    // 'diverging_2': labels, left values, right values
    var map = {
        bar:'labels_only', h_bar:'labels_only', pie:'labels_only', funnel:'labels_only',
        progress:'labels_only', radar:'labels_only', treemap:'labels_only',
        grouped:'multi_series', stacked:'multi_series', line:'multi_series', area:'multi_series',
        dual_axis:'multi_series', scatter:'multi_series', bubble:'multi_series',
        boxplot:'multi_series', diverging:'multi_series',
        heatmap:'heatmap_grid', gantt:'multi_series',
        waterfall:'labels_only', gauge:'gauge_1', donut:'donut_center'
    };
    return map[type] || 'labels_only';
}

function _buildTable(type, config) {
    var shape = _getTableShape(type);
    var html = '<table>';
    // Helper: build <input type="text"> with properly escaped value
    function _inp(val) {
        return '<input type="text" value="' + esc(String(val !== undefined && val !== null ? val : '')) + '">';
    }

    if (shape === 'gauge_1') {
        html += '<tr><th>指标</th><th>值</th><th>最大值</th><th>单位</th></tr>';
        html += '<tr>';
        html += '<td>' + _inp(config.labels[0] || '') + '</td>';
        html += '<td>' + _inp(config.series[0].values[0] || 0) + '</td>';
        html += '<td>' + _inp(config.max || 100) + '</td>';
        html += '<td>' + _inp(config.unit || '%') + '</td>';
        html += '</tr>';
    } else if (shape === 'donut_center') {
        html += '<tr><th></th>';
        for (var i = 0; i < config.labels.length; i++) html += '<th>' + _inp(config.labels[i]) + '</th>';
        html += '</tr>';
        html += '<tr><td style="font-weight:bold;background:#f1f5f9">' + esc(config.series[0].name) + '</td>';
        for (var i = 0; i < config.labels.length; i++) html += '<td>' + _inp(i < config.series[0].values.length ? config.series[0].values[i] : 0) + '</td>';
        html += '</tr>';
    } else if (shape === 'heatmap_grid') {
        var colLabels = config.colLabels || config.labels;
        var rowLabels = config.labels;
        var nC = colLabels.length, nR = rowLabels.length;
        html += '<tr><th></th>';
        for (var c = 0; c < nC; c++) html += '<th>' + _inp(colLabels[c]) + '</th>';
        html += '</tr>';
        for (var r = 0; r < nR; r++) {
            html += '<tr><td style="font-weight:bold;background:#f1f5f9">' + _inp(rowLabels[r]) + '</td>';
            for (var c2 = 0; c2 < nC; c2++) {
                var idx = r * nC + c2;
                html += '<td>' + _inp(config.series[0].values[idx] || 0) + '</td>';
            }
            html += '</tr>';
        }
    } else if (shape === 'labels_only') {
        html += '<tr><th></th>';
        for (var i = 0; i < config.labels.length; i++) html += '<th>' + _inp(config.labels[i]) + '</th>';
        html += '</tr>';
        html += '<tr><td style="font-weight:bold;background:#f1f5f9">' + esc(config.series[0].name) + '</td>';
        for (var i = 0; i < config.labels.length; i++) html += '<td>' + _inp(i < config.series[0].values.length ? config.series[0].values[i] : 0) + '</td>';
        html += '</tr>';
    } else {
        // multi_series: header = blank + labels, rows = series
        html += '<tr><th></th>';
        for (var i = 0; i < config.labels.length; i++) html += '<th>' + _inp(config.labels[i]) + '</th>';
        html += '</tr>';
        for (var si = 0; si < config.series.length; si++) {
            html += '<tr><td style="font-weight:bold;background:#f1f5f9">' + _inp(config.series[si].name) + '</td>';
            for (var i = 0; i < config.labels.length; i++) html += '<td>' + _inp(i < config.series[si].values.length ? config.series[si].values[i] : 0) + '</td>';
            html += '</tr>';
        }
    }
    html += '</table>';
    return html;
}

function _readTable(type, config) {
    var tbl = document.querySelector('#cem-table-wrap table');
    if (!tbl) return config;
    var shape = _getTableShape(type);
    var newCfg = JSON.parse(JSON.stringify(config));
    // Helper: read value from a cell — prefers <input> value over textContent
    function _cv(cell) {
        var inp = cell ? cell.querySelector('input') : null;
        return inp ? inp.value : (cell ? cell.textContent : '');
    }

    if (shape === 'gauge_1') {
        var cells = tbl.rows[1].cells;
        newCfg.labels = [_cv(cells[0]).trim()];
        newCfg.series = [{name: '值', values: [parseFloat(_cv(cells[1])) || 0]}];
        newCfg.max = parseFloat(_cv(cells[2])) || 100;
        newCfg.unit = _cv(cells[3]).trim() || '%';
    } else if (shape === 'heatmap_grid') {
        var colLabels = [], rowLabels = [];
        var headerCells = tbl.rows[0].cells;
        for (var c = 1; c < headerCells.length; c++) colLabels.push(_cv(headerCells[c]).trim());
        var vals = [];
        for (var r = 1; r < tbl.rows.length; r++) {
            rowLabels.push(_cv(tbl.rows[r].cells[0]).trim());
            for (var c = 1; c < tbl.rows[r].cells.length; c++) vals.push(parseFloat(_cv(tbl.rows[r].cells[c])) || 0);
        }
        newCfg.labels = rowLabels;
        newCfg.colLabels = colLabels;
        newCfg.series = [{name: '值', values: vals}];
    } else {
        // Handles labels_only, multi_series, and all other shapes
        var headerCells = tbl.rows[0].cells;
        var labels = [];
        for (var c = 1; c < headerCells.length; c++) labels.push(_cv(headerCells[c]).trim());
        newCfg.labels = labels;
        var series = [];
        for (var r = 1; r < tbl.rows.length; r++) {
            var name = _cv(tbl.rows[r].cells[0]).trim();
            var values = [];
            for (var c = 1; c < tbl.rows[r].cells.length; c++) values.push(parseFloat(_cv(tbl.rows[r].cells[c])) || 0);
            series.push({name: name, values: values});
        }
        newCfg.series = series;
    }

    newCfg.title = document.getElementById('cem-chart-title').value || newCfg.title;
    return newCfg;
}

function _saveChart() {
    if (!_editTarget) return;
    var type = _editTarget.getAttribute('data-chart-type');
    var oldCfg = JSON.parse(_editTarget.getAttribute('data-chart-config') || '{}');
    var newCfg = _readTable(type, oldCfg);

    // Read extra fields
    if (type === 'donut') {
        var ctEl = document.getElementById('cem-center-text');
        var clEl = document.getElementById('cem-center-label');
        if (ctEl) newCfg.centerText = ctEl.value;
        if (clEl) newCfg.centerLabel = clEl.value;
    }

    // Render new SVG
    var renderer = R[type];
    if (!renderer) { _closeModal(); return; }
    _normalizeConfig(type, newCfg);
    var newSvg = renderer(newCfg);
    // Update chart container
    _editTarget.innerHTML = newSvg;
    _editTarget.setAttribute('data-chart-config', JSON.stringify(newCfg));

    _closeModal();

    // Trigger content report
    if (typeof scheduleContentReport === 'function') scheduleContentReport();
}

// ── Public: open chart editor ──
window._openChartEditor = function(chartEl) {
    if (!chartEl) return;
    if (!_editModal) _createModal();
    _editTarget = chartEl;
    var type = chartEl.getAttribute('data-chart-type');
    if (!type) {
        console.warn('Chart has no data-chart-type attribute');
        return;
    }
    var configStr = chartEl.getAttribute('data-chart-config');
    var config;
    try {
        config = JSON.parse(configStr);
    } catch(e) {
        console.error('Failed to parse chart config:', e, configStr);
        return;
    }
    if (!config || !config.labels || !config.series) {
        console.warn('Invalid chart config', config);
        return;
    }

    _editType = type;
    _editConfig = JSON.parse(JSON.stringify(config)); // deep clone

    document.getElementById('cem-chart-title').value = config.title || '';

    // Extra fields
    var extraEl = document.getElementById('cem-extra-fields');
    extraEl.innerHTML = '';
    if (type === 'donut') {
        extraEl.innerHTML =
            '<label>中心文字</label><input type="text" id="cem-center-text" value="' + esc(config.centerText || '') + '" style="width:48%;margin-right:4%;display:inline-block;padding:7px 10px;border:1px solid #cbd5e1;border-radius:6px;font-size:14px;" />' +
            '<input type="text" id="cem-center-label" value="' + esc(config.centerLabel || '') + '" placeholder="副标签" style="width:48%;display:inline-block;padding:7px 10px;border:1px solid #cbd5e1;border-radius:6px;font-size:14px;" />';
        // 监听额外字段输入
        setTimeout(function() {
            var ct = document.getElementById('cem-center-text');
            var cl = document.getElementById('cem-center-label');
            if (ct) ct.addEventListener('input', function() { _scheduleLivePreview(); });
            if (cl) cl.addEventListener('input', function() { _scheduleLivePreview(); });
        }, 50);
    }

    document.getElementById('cem-table-wrap').innerHTML = _buildTable(type, config);
    _editModal.style.display = 'flex';

    // 立即显示实时预览
    _updateLivePreview();
};

// ── Inline (floating) cell editor ──
var _inlineInput = null;
var _inlineDebounceTimer = null;
var _inlineOriginalValue = null;
var _inlineChartEl = null;
var _inlineCeKey = null;

function _getCeValue(ceKey, config) {
    if (ceKey === 'title') return config.title || '';
    if (ceKey === 'centerText') return config.centerText || '';
    if (ceKey === 'centerLabel') return config.centerLabel || '';
    if (ceKey === 'xLabel') return config.xLabel || '';
    if (ceKey === 'yLabel') return config.yLabel || '';
    var m;
    m = ceKey.match(/^label:(\d+)$/);
    if (m) { var i = parseInt(m[1]); return config.labels && config.labels[i] !== undefined ? String(config.labels[i]) : ''; }
    m = ceKey.match(/^col:(\d+)$/);
    if (m) { var i = parseInt(m[1]); return config.colLabels && config.colLabels[i] !== undefined ? String(config.colLabels[i]) : ''; }
    m = ceKey.match(/^sname:(\d+)$/);
    if (m) { var si = parseInt(m[1]); return config.series && config.series[si] ? config.series[si].name || '' : ''; }
    m = ceKey.match(/^val:(\d+):(\d+)$/);
    if (m) { var si2 = parseInt(m[1]), idx = parseInt(m[2]); return config.series && config.series[si2] ? String(config.series[si2].values[idx] !== undefined ? config.series[si2].values[idx] : '') : ''; }
    return '';
}

function _setCeValue(ceKey, value, config) {
    if (ceKey === 'title') { config.title = value; return; }
    if (ceKey === 'centerText') { config.centerText = value; return; }
    if (ceKey === 'centerLabel') { config.centerLabel = value; return; }
    if (ceKey === 'xLabel') { config.xLabel = value; return; }
    if (ceKey === 'yLabel') { config.yLabel = value; return; }
    var m;
    m = ceKey.match(/^label:(\d+)$/);
    if (m) { var i = parseInt(m[1]); if (config.labels) config.labels[i] = value; return; }
    m = ceKey.match(/^col:(\d+)$/);
    if (m) { var i = parseInt(m[1]); if (config.colLabels) config.colLabels[i] = value; return; }
    m = ceKey.match(/^sname:(\d+)$/);
    if (m) { var si = parseInt(m[1]); if (config.series && config.series[si]) config.series[si].name = value; return; }
    m = ceKey.match(/^val:(\d+):(\d+)$/);
    if (m) {
        var si2 = parseInt(m[1]), idx = parseInt(m[2]);
        if (config.series && config.series[si2]) {
            var num = parseFloat(value);
            config.series[si2].values[idx] = isNaN(num) ? 0 : num;
        }
        return;
    }
}

function _closeInlineEdit() {
    if (!_inlineInput) return;
    var inp = _inlineInput;
    _inlineInput = null;
    _inlineChartEl = null;
    _inlineCeKey = null;
    _inlineOriginalValue = null;
    if (_inlineDebounceTimer) { clearTimeout(_inlineDebounceTimer); _inlineDebounceTimer = null; }
    if (inp.parentNode) inp.parentNode.removeChild(inp);
}

function _applyInlineEdit(chartEl, ceKey, value) {
    var configStr = chartEl.getAttribute('data-chart-config');
    if (!configStr) return;
    var config;
    try { config = JSON.parse(configStr); } catch(e) { return; }
    var type = chartEl.getAttribute('data-chart-type');
    if (!type || !R[type]) return;
    _setCeValue(ceKey, value, config);
    _normalizeConfig(type, config);
    chartEl.innerHTML = R[type](config);
    chartEl.setAttribute('data-chart-config', JSON.stringify(config));
    if (typeof scheduleContentReport === 'function') scheduleContentReport();
}

// ── Public: re-render all charts to add data-ce attributes ──
window._rerenderAllCharts = function() {
    var containers = document.querySelectorAll('.chart-container[data-chart-type]');
    for (var i = 0; i < containers.length; i++) {
        var el = containers[i];
        var type = el.getAttribute('data-chart-type');
        var configStr = el.getAttribute('data-chart-config');
        if (!type || !configStr || !R[type]) continue;
        try {
            var config = JSON.parse(configStr);
            if (!config || !config.labels || !config.series) continue;
            _normalizeConfig(type, config);
            el.innerHTML = R[type](config);
            el.contentEditable = 'false';
        } catch(e) {
            console.warn('_rerenderAllCharts: failed for', type, e);
        }
    }
};

window._openInlineEdit = function(chartEl, ceEl) {
    _closeInlineEdit();
    var ceKey = ceEl.getAttribute('data-ce');
    if (!ceKey) return;
    var configStr = chartEl.getAttribute('data-chart-config');
    if (!configStr) return;
    var config;
    try { config = JSON.parse(configStr); } catch(e) { return; }
    var currentValue = _getCeValue(ceKey, config);
    _inlineOriginalValue = currentValue;
    _inlineChartEl = chartEl;
    _inlineCeKey = ceKey;
    var rect = ceEl.getBoundingClientRect();
    var svgEl = ceEl.ownerSVGElement;
    var svgRect = svgEl ? svgEl.getBoundingClientRect() : rect;
    var svgVBW = svgEl ? parseFloat((svgEl.getAttribute('viewBox') || '0 0 500 300').split(' ')[2]) : 500;
    var scale = svgVBW > 0 ? svgRect.width / svgVBW : 1;
    var rawFS = parseFloat(ceEl.getAttribute('font-size') || '14');
    var fontSize = Math.max(11, Math.round(rawFS * scale));
    var anchor = ceEl.getAttribute('text-anchor') || 'start';
    var inputWidth = Math.max(60, rect.width + 20);
    var left = rect.left;
    if (anchor === 'middle') left = rect.left + rect.width / 2 - inputWidth / 2;
    else if (anchor === 'end') left = rect.right - inputWidth;
    var inp = document.createElement('input');
    inp.type = 'text';
    inp.value = currentValue;
    inp.style.cssText = [
        'position:fixed',
        'left:' + Math.round(left) + 'px',
        'top:' + Math.round(rect.top - 2) + 'px',
        'width:' + Math.round(inputWidth) + 'px',
        'height:' + Math.round(Math.max(20, rect.height + 4)) + 'px',
        'font-size:' + fontSize + 'px',
        'font-family:"Microsoft YaHei",sans-serif',
        'border:2px solid #4a90d9',
        'border-radius:4px',
        'background:rgba(255,255,255,0.97)',
        'color:#1e293b',
        'padding:0 4px',
        'box-sizing:border-box',
        'z-index:20000',
        'outline:none',
        'text-align:' + (anchor === 'end' ? 'right' : anchor === 'middle' ? 'center' : 'left'),
        'box-shadow:0 2px 8px rgba(74,144,217,0.25)'
    ].join(';');
    inp.addEventListener('input', function() {
        if (_inlineDebounceTimer) clearTimeout(_inlineDebounceTimer);
        _inlineDebounceTimer = setTimeout(function() {
            _inlineDebounceTimer = null;
            if (_inlineChartEl) _applyInlineEdit(_inlineChartEl, _inlineCeKey, inp.value);
        }, 300);
    });
    inp.addEventListener('blur', function() {
        if (!_inlineInput) return;
        var val = inp.value;
        var cel = _inlineChartEl;
        var cek = _inlineCeKey;
        _closeInlineEdit();
        if (cel) _applyInlineEdit(cel, cek, val);
    });
    inp.addEventListener('keydown', function(e) {
        e.stopPropagation();
        if (e.key === 'Enter') { inp.blur(); }
        if (e.key === 'Escape') {
            if (_inlineDebounceTimer) { clearTimeout(_inlineDebounceTimer); _inlineDebounceTimer = null; }
            var origVal = _inlineOriginalValue;
            var cel = _inlineChartEl;
            var cek = _inlineCeKey;
            _closeInlineEdit();
            if (cel) _applyInlineEdit(cel, cek, origVal);
        }
    });
    document.body.appendChild(inp);
    _inlineInput = inp;
    inp.focus();
    inp.select();
};


})();
