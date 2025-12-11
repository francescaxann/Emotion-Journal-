// Minimal Chart fallback implementation
// Provides a tiny `Chart` constructor used by our history page when the CDN is blocked.
// This is NOT Chart.js and like it's a lightweight renderer that supports the subset we use:
// - type: 'line' :D
// - data: { labels: [...], datasets: [{ data: [...], borderColor, backgroundColor, pointBackgroundColor }] }
// - options: { scales: { y: { min, max } } }
(function(){
  // Enhanced fallback: draws grid lines, axis ticks, a small legend, and a DOM tooltip.
  function createTooltip(){
    var tip = document.createElement('div');
    tip.id = 'chart-tooltip';
    Object.assign(tip.style, {
      position: 'absolute', pointerEvents: 'none', background: 'rgba(17,24,39,0.95)', color: '#fff',
      padding: '8px 10px', borderRadius: '6px', fontSize: '12px', display: 'none', zIndex: 9999,
      boxShadow: '0 4px 10px rgba(2,6,23,0.3)'
    });
    document.body.appendChild(tip);
    return tip;
  }

  function drawLineChart(canvas, config, state){
    var ctx = canvas.getContext('2d');
    var dpr = window.devicePixelRatio || 1;
    var width = canvas.clientWidth || 800;
    var height = canvas.clientHeight || 240;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    ctx.scale(dpr, dpr);
    ctx.clearRect(0,0,width,height);
    var padding = 44;
    var plotW = Math.max(10, width - padding*2);
    var plotH = Math.max(10, height - padding*2);
    var labels = (config.data && config.data.labels) || [];
    var datasets = (config.data && config.data.datasets) || [];
    // apply visibility from state
    datasets = datasets.map(function(ds, i){
      var copy = Object.assign({}, ds);
      if (state && state.hidden && state.hidden[i]) copy._hidden = true;
      return copy;
    });
    var yMin = (config.options && config.options.scales && config.options.scales.y && config.options.scales.y.min) || 0;
    var yMax = (config.options && config.options.scales && config.options.scales.y && config.options.scales.y.max) || 100;
    function xFor(i){ return padding + (labels.length>1 ? (i/(labels.length-1))*plotW : plotW/2); }
    function yFor(v){ var range = (yMax - yMin) || 1; return padding + plotH - ((v - yMin)/range)*plotH; }

    // background
    ctx.fillStyle = '#fff'; ctx.fillRect(0,0,width,height);

    // horizontal grid & y ticks
    ctx.strokeStyle = '#eef2f6'; ctx.lineWidth = 1;
    ctx.fillStyle = '#526070'; ctx.font = '11px sans-serif'; ctx.textAlign = 'right';
    var ticks = [yMin, (yMin+yMax)/2, yMax];
    for(var t=0;t<ticks.length;t++){
      var val = ticks[t];
      var yy = yFor(val);
      ctx.beginPath(); ctx.moveTo(padding, yy); ctx.lineTo(padding+plotW, yy); ctx.stroke();
      ctx.fillText(String(Math.round(val)), padding-8, yy+4);
    }

    // x axis baseline
    ctx.strokeStyle = '#e6edf0'; ctx.beginPath(); ctx.moveTo(padding, padding+plotH); ctx.lineTo(padding+plotW, padding+plotH); ctx.stroke();

    // store point positions for interaction
    var pointPositions = [];

    datasets.forEach(function(ds, di){
      var data = ds.data || [];
      if (ds._hidden) return; // skip hidden datasets
      ctx.strokeStyle = ds.borderColor || '#4b9b8e';
      ctx.lineWidth = 2;
      ctx.beginPath();
      var started = false;
      for(var i=0;i<data.length;i++){
        var v = data[i];
        if (v===null || typeof v==='undefined') { started = false; pointPositions.push(null); continue; }
        var x = xFor(i), y = yFor(v);
        if (!started){ ctx.moveTo(x,y); started = true; } else { ctx.lineTo(x,y); }
        pointPositions[i] = pointPositions[i] || [];
        pointPositions[i][di] = { x: x, y: y, v: v, color: Array.isArray(ds.pointBackgroundColor)? (ds.pointBackgroundColor[i]||ds.borderColor) : (ds.pointBackgroundColor||ds.borderColor) };
      }
      ctx.stroke();

      // draw points
      for(var j=0;j<data.length;j++){
        var val = data[j]; if (val===null||typeof val==='undefined') continue;
        var px = xFor(j), py = yFor(val);
        ctx.beginPath();
        var color = (Array.isArray(ds.pointBackgroundColor) ? (ds.pointBackgroundColor[j]||ds.borderColor) : (ds.pointBackgroundColor || ds.borderColor)) || '#222';
        ctx.fillStyle = color;
        ctx.arc(px, py, ds.pointRadius||4, 0, Math.PI*2);
        ctx.fill();
      }
    });

    // x labels
    ctx.fillStyle = '#667085'; ctx.font = '11px sans-serif'; ctx.textAlign = 'center';
    for(var k=0;k<labels.length;k++){
      var lx = xFor(k); ctx.fillText(labels[k], lx, padding + plotH + 16);
    }

    // legend is rendered as DOM elements for interactivity (click to toggle)
    // remove any existing legend container for this canvas
    var wrap = canvas.parentNode;
    var existing = wrap.querySelector('.fallback-legend');
    if (existing) existing.remove();
    var legend = document.createElement('div');
    legend.className = 'fallback-legend';
    Object.assign(legend.style, { position: 'absolute', right: '12px', top: (canvas.offsetTop + 6) + 'px', background: 'transparent', fontFamily: 'sans-serif', fontSize: '12px', color: '#334155', display: 'flex', flexDirection: 'column', gap: '6px', pointerEvents: 'auto' });
    // create items for every dataset (even hidden ones so users can toggle back on)
    datasets = (config.data && config.data.datasets) || [];
    datasets.forEach(function(ds, i){
      var item = document.createElement('div');
      Object.assign(item.style, { display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', userSelect: 'none' });
      var box = document.createElement('span');
      Object.assign(box.style, { width: '12px', height: '12px', display: 'inline-block', borderRadius: '3px', background: ds.borderColor || '#333' });
      var lbl = document.createElement('span'); lbl.textContent = ds.label || ('series ' + (i+1));
      item.appendChild(box); item.appendChild(lbl);
      // reflect current hidden state
      if (state && state.hidden && state.hidden[i]){ item.style.opacity = '0.35'; }
      (function(idx, el){
        el.addEventListener('click', function(){
          state.hidden = state.hidden || {};
          state.hidden[idx] = !state.hidden[idx];
          // toggle visual
          el.style.opacity = state.hidden[idx] ? '0.35' : '1';
          // redraw chart
          drawLineChart(canvas, config, state);
        });
      })(i, item);
      legend.appendChild(item);
    });
    // attach legend; position wrapper relatively if needed
    if (getComputedStyle(wrap).position === 'static') wrap.style.position = 'relative';
    wrap.appendChild(legend);

    // store render state on canvas so callers (and event handlers) can read it
    var renderState = { points: pointPositions };
    try { canvas._fallbackRenderState = renderState; } catch (e) {}
    return renderState;
  }

  var tooltip = null;
  window.Chart = function(ctxOrCanvas, config){
    var canvas = (ctxOrCanvas && ctxOrCanvas.canvas) ? ctxOrCanvas.canvas : ctxOrCanvas;
    if (typeof canvas === 'string') canvas = document.getElementById(canvas);
    if (!canvas) return;

    // persistent state for visibility toggles
    var stateObj = canvas._fallbackState || { hidden: {} };
    canvas._fallbackState = stateObj;

    // initial draw
    drawLineChart(canvas, config, stateObj);

    // ensure tooltip DOM exists
    if (!tooltip) tooltip = createTooltip();

    function findNearest(mx, my){
      var s = canvas._fallbackRenderState;
      if (!s || !s.points) return null;
      var best = { dist: Infinity, info: null };
      for(var i=0;i<s.points.length;i++){
        var arr = s.points[i]; if (!arr) continue;
        for(var j=0;j<arr.length;j++){
          var p = arr[j]; if (!p) continue;
          var dx = p.x - mx, dy = p.y - my; var d = Math.sqrt(dx*dx+dy*dy);
          if (d < best.dist){ best = { dist: d, info: { idx: i, series: j, px: p.x, py: p.y, v: p.v, color: p.color } }; }
        }
      }
      return best.dist < 12 ? best.info : null;
    }

    function onMove(e){
      var rect = canvas.getBoundingClientRect();
      var mx = e.clientX - rect.left, my = e.clientY - rect.top;
      var hit = findNearest(mx, my);
      if (hit){
        tooltip.style.display = 'block';
        tooltip.innerHTML = '<strong>' + (config.data.labels[hit.idx]||'') + '</strong><div style="font-size:12px;margin-top:4px;color:#e2e8f0">Value: ' + hit.v + '</div>';
        tooltip.style.left = (rect.left + hit.px + 12) + 'px';
        tooltip.style.top = (rect.top + hit.py - 8) + 'px';
        tooltip.style.borderLeft = '4px solid ' + (hit.color || '#444');
      } else {
        tooltip.style.display = 'none';
      }
    }

    function onOut(){ if (tooltip) tooltip.style.display = 'none'; }

    canvas.addEventListener('mousemove', onMove);
    canvas.addEventListener('mouseout', onOut);

    this.destroy = function(){
      canvas.removeEventListener('mousemove', onMove);
      canvas.removeEventListener('mouseout', onOut);
      if (tooltip){ tooltip.style.display = 'none'; }
    };
  };
})();
