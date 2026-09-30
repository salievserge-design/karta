/* =================================================================
   Карта объекта М-4 «Дон» — сборка листа
   ================================================================= */
(function () {
  'use strict';

  var D = window.KARTA;
  var S = Object.assign({}, D.defaults);
  var maps = {};          // main, i1, i2
  var layers = {};        // подложки
  var objLayers = [];     // слои объектов на обзорной карте
  var routeLayer = null, regionLayer = null, cityLayer = null;
  var geom = { main: null, alt: null };
  var LS = window.localStorage;

  /* ---------------- утилиты ---------------- */

  function $(id) { return document.getElementById(id); }

  function toast(msg, ms) {
    var t = $('toast');
    t.textContent = msg;
    t.classList.add('on');
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { t.classList.remove('on'); }, ms || 2600);
  }

  /* декодер encoded polyline (Google/OSRM, precision 5) */
  function decodePolyline(str, precision) {
    var index = 0, lat = 0, lng = 0, coords = [],
        shift, result, byte, factor = Math.pow(10, precision || 5);
    while (index < str.length) {
      shift = 0; result = 0;
      do { byte = str.charCodeAt(index++) - 63; result |= (byte & 0x1f) << shift; shift += 5; } while (byte >= 0x20);
      lat += (result & 1) ? ~(result >> 1) : (result >> 1);
      shift = 0; result = 0;
      do { byte = str.charCodeAt(index++) - 63; result |= (byte & 0x1f) << shift; shift += 5; } while (byte >= 0x20);
      lng += (result & 1) ? ~(result >> 1) : (result >> 1);
      coords.push([lat / factor, lng / factor]);
    }
    return coords;
  }

  function cacheGet(k) {
    try { var v = LS.getItem(k); return v ? JSON.parse(v) : null; } catch (e) { return null; }
  }
  function cacheSet(k, v) {
    try { LS.setItem(k, JSON.stringify(v)); } catch (e) { /* quota */ }
  }

  /* ---------------- подложки ---------------- */

  function makeBase(key) {
    var b = D.basemaps[key];
    return L.tileLayer(b.url, {
      maxZoom: b.maxZoom || 19,
      maxNativeZoom: b.maxZoom || 19,
      subdomains: b.subdomains || 'abc',
      crossOrigin: true,
      attribution: b.attribution
    });
  }

  function setBase(mapKey, baseKey) {
    var m = maps[mapKey];
    if (!m) return;
    if (layers[mapKey]) m.removeLayer(layers[mapKey]);
    layers[mapKey] = makeBase(baseKey).addTo(m);
    layers[mapKey].bringToBack();
  }

  /* ---------------- значки объектов ---------------- */

  /* короткий красный пунктирный штрих «место производства работ» */
  function worksIcon(axisDeg, len, weight) {
    var w = len + 12, h = 26;
    var svg =
      '<svg width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + ' ' + h + '" ' +
      'style="transform:rotate(' + (axisDeg - 90) + 'deg);transform-origin:50% 50%;overflow:visible">' +
      '<line x1="6" y1="' + h / 2 + '" x2="' + (w - 6) + '" y2="' + h / 2 + '" ' +
      'stroke="#ffffff" stroke-width="' + (weight + 3) + '" stroke-linecap="round"/>' +
      '<line x1="6" y1="' + h / 2 + '" x2="' + (w - 6) + '" y2="' + h / 2 + '" ' +
      'stroke="#cc0f24" stroke-width="' + weight + '" stroke-linecap="round" ' +
      'stroke-dasharray="' + (weight * 1.9) + ' ' + (weight * 1.5) + '"/>' +
      '</svg>';
    return L.divIcon({ className: '', html: svg, iconSize: [w, h], iconAnchor: [w / 2, h / 2] });
  }

  function badgeIcon(n) {
    return L.divIcon({
      className: '',
      html: '<div class="obj-badge">' + n + '</div>',
      iconSize: [26, 26],
      iconAnchor: [13, 13]
    });
  }

  /* ---------------- обзорная карта ---------------- */

  function buildMain() {
    maps.main = L.map('mainmap', {
      zoomControl: false,
      attributionControl: false,
      zoomSnap: 0.25,
      zoomDelta: 0.25,
      preferCanvas: false
    });
    setBase('main', S.overviewBase);
    fitOverview();

    maps.main.on('move zoom moveend zoomend resize', updateLeaders);
  }

  function fitOverview() {
    maps.main.fitBounds(D.overview.bounds, {
      paddingTopLeft: D.overview.paddingTopLeft,
      paddingBottomRight: currentPadBR(),
      animate: false
    });
  }

  function currentPadBR() {
    var p = D.overview.paddingBottomRight.slice();
    if (S.sheet === 'a4') { p[0] = Math.round(p[0] * 0.72); p[1] = Math.round(p[1] * 0.72); }
    return p;
  }

  /* ---------------- объекты на обзорной карте ---------------- */

  function drawObjects() {
    objLayers.forEach(function (l) { maps.main.removeLayer(l); });
    objLayers = [];
    D.objects.forEach(function (o) {
      var works = L.marker([o.lat, o.lon], {
        icon: worksIcon(o.axis, 34, 4), interactive: false, zIndexOffset: 400
      }).addTo(maps.main);

      var ring = L.circleMarker([o.lat, o.lon], {
        radius: 15, color: '#cc0f24', weight: 2, opacity: .95,
        fillColor: '#cc0f24', fillOpacity: .10, dashArray: '4 3', interactive: false
      }).addTo(maps.main);

      var badge = L.marker([o.lat, o.lon], {
        icon: badgeIcon(o.n), draggable: true, zIndexOffset: 800,
        title: 'Объект ' + o.n + ' · ' + o.km + ' — можно перетащить'
      }).addTo(maps.main);

      badge.on('drag', function (e) {
        var ll = e.target.getLatLng();
        o.lat = +ll.lat.toFixed(5); o.lon = +ll.lng.toFixed(5);
        works.setLatLng(ll); ring.setLatLng(ll);
        syncInputs(); updateLeaders();
      });
      badge.on('dragend', function () { refreshInsets(); renderLegend(); });

      objLayers.push(works, ring, badge);
    });
  }

  /* ---------------- выноски ---------------- */

  function insetGeometry() {
    var a4 = S.sheet === 'a4';
    var W = a4 ? 1122 : 1587;
    var d = a4 ? 288 : 430;
    var right = a4 ? 22 : 40;
    var tops = a4 ? [86, 400] : [112, 578];
    return { W: W, d: d, right: right, tops: tops };
  }

  function buildInsets() {
    var g = insetGeometry();
    D.objects.forEach(function (o, i) {
      var id = 'inset' + o.n;
      var el = $(id);
      if (!el) {
        el = document.createElement('div');
        el.id = id;
        el.className = 'inset';
        el.innerHTML = '<div class="lmap" id="' + id + '-map"></div>' +
                       '<div class="inset-num">' + o.n + '</div>';
        $('sheet').appendChild(el);

        var cap = document.createElement('div');
        cap.className = 'inset-cap';
        cap.id = id + '-cap';
        $('sheet').appendChild(cap);
      }
      el.style.width = el.style.height = g.d + 'px';
      el.style.right = g.right + 'px';
      el.style.top = g.tops[i] + 'px';

      var capEl = $(id + '-cap');
      capEl.textContent = o.insetCaption;
      capEl.style.right = g.right + 'px';
      capEl.style.top = (g.tops[i] + g.d + 7) + 'px';

      if (!maps['i' + o.n]) {
        var m = L.map(id + '-map', {
          zoomControl: false, attributionControl: false,
          scrollWheelZoom: false, doubleClickZoom: false,
          zoomSnap: 0.25, zoomDelta: 0.25
        });
        maps['i' + o.n] = m;
        setBase('i' + o.n, S.insetBase);
        m.setView([o.lat, o.lon], o.inset.zoom);

        L.marker([o.lat, o.lon], { icon: worksIcon(o.axis, 96, 7), interactive: false }).addTo(m);
        L.circleMarker([o.lat, o.lon], {
          radius: 34, color: '#cc0f24', weight: 2.5, opacity: .95,
          fillOpacity: 0, dashArray: '6 5', interactive: false
        }).addTo(m);
        maps['i' + o.n]._objMarkers = true;
      }
      maps['i' + o.n].invalidateSize(false);
    });
  }

  function refreshInsets() {
    D.objects.forEach(function (o) {
      var m = maps['i' + o.n];
      if (!m) return;
      m.eachLayer(function (l) {
        if (l instanceof L.Marker || l instanceof L.CircleMarker) l.setLatLng([o.lat, o.lon]);
      });
      m.setView([o.lat, o.lon], o.inset.zoom, { animate: false });
      m.invalidateSize(false);
    });
    updateLeaders();
  }

  /* ---------------- выносные линии ---------------- */

  function updateLeaders() {
    var svg = $('leaders');
    var sheet = $('sheet').getBoundingClientRect();
    var g = insetGeometry();
    svg.setAttribute('viewBox', '0 0 ' + g.W + ' ' + $('sheet').offsetHeight);
    svg.setAttribute('width', $('sheet').offsetWidth);
    svg.setAttribute('height', $('sheet').offsetHeight);

    var scale = sheet.width / $('sheet').offsetWidth || 1;
    var parts = ['<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" ' +
      'markerWidth="6" markerHeight="6" orient="auto-start-reverse">' +
      '<path d="M0,0 L10,5 L0,10 z" fill="#8e1420"/></marker></defs>'];

    D.objects.forEach(function (o, i) {
      var el = $('inset' + o.n);
      if (!el || !maps.main) return;
      var r = el.getBoundingClientRect();
      var cx = (r.left - sheet.left) / scale + el.offsetWidth / 2;
      var cy = (r.top - sheet.top) / scale + el.offsetHeight / 2;
      var rad = el.offsetWidth / 2 + 4;

      var p = maps.main.latLngToContainerPoint([o.lat, o.lon]);
      var dx = p.x - cx, dy = p.y - cy;
      var len = Math.hypot(dx, dy) || 1;
      if (len < rad + 10) return;                  // выноска накрывает объект
      var sx = cx + dx / len * rad, sy = cy + dy / len * rad;
      var ex = p.x - dx / len * 17, ey = p.y - dy / len * 17;

      parts.push(
        '<line x1="' + sx + '" y1="' + sy + '" x2="' + ex + '" y2="' + ey + '" ' +
        'stroke="#ffffff" stroke-width="4.5" stroke-linecap="round" opacity="0.85"/>' +
        '<line x1="' + sx + '" y1="' + sy + '" x2="' + ex + '" y2="' + ey + '" ' +
        'stroke="#8e1420" stroke-width="1.8" stroke-linecap="round" marker-end="url(#ar)"/>'
      );
    });
    svg.innerHTML = parts.join('');
  }

  /* ---------------- трассы ---------------- */

  function drawRoutes() {
    if (routeLayer) { maps.main.removeLayer(routeLayer); routeLayer = null; }
    if (!S.showRoutes) return;
    routeLayer = L.layerGroup().addTo(maps.main);

    if (geom.main) {
      L.polyline(geom.main, {
        color: '#ffffff', weight: 8, opacity: .55, lineCap: 'round', interactive: false
      }).addTo(routeLayer);
      L.polyline(geom.main, {
        color: '#cc0f24', weight: 3.4, opacity: .92, lineCap: 'round', interactive: false
      }).addTo(routeLayer);
    }
    if (geom.alt) {
      L.polyline(geom.alt, {
        color: '#ffffff', weight: 7, opacity: .55, lineCap: 'round', interactive: false
      }).addTo(routeLayer);
      L.polyline(geom.alt, {
        color: '#cc0f24', weight: 2.8, opacity: .92, dashArray: '9 6',
        lineCap: 'round', interactive: false
      }).addTo(routeLayer);
    }
    routeLayer.eachLayer(function (l) { l.bringToBack(); });
    if (layers.main) layers.main.bringToBack();
  }

  function loadRoutes() {
    geom.main = decodePolyline(D.routes.main);
    geom.alt = decodePolyline(D.routes.alt);
    drawRoutes();

    var cached = cacheGet('karta.routes.v1');
    if (cached && cached.main && cached.alt) {
      geom.main = cached.main; geom.alt = cached.alt; drawRoutes(); return;
    }
    Promise.all([
      fetch(D.routes.osrmMain).then(function (r) { return r.json(); }),
      fetch(D.routes.osrmAlt).then(function (r) { return r.json(); })
    ]).then(function (res) {
      if (res[0].code !== 'Ok' || res[1].code !== 'Ok') return;
      geom.main = decodePolyline(res[0].routes[0].geometry);
      geom.alt = decodePolyline(res[1].routes[0].geometry);
      cacheSet('karta.routes.v1', { main: geom.main, alt: geom.alt });
      drawRoutes();
    }).catch(function () {
      /* нет сети до OSRM — остаётся генерализованная геометрия */
    });
  }

  /* ---------------- границы субъектов ---------------- */

  function drawRegions(gj) {
    if (regionLayer) { maps.main.removeLayer(regionLayer); regionLayer = null; }
    if (!S.showRegions || !gj) return;
    regionLayer = L.geoJSON(gj, {
      style: { color: '#8e1420', weight: 1.8, opacity: .8, dashArray: '7 4', fill: false },
      interactive: false
    }).addTo(maps.main);
    regionLayer.bringToBack();
    if (routeLayer) routeLayer.eachLayer(function (l) { l.bringToBack(); });
    if (layers.main) layers.main.bringToBack();
  }

  function loadRegions() {
    var cached = cacheGet('karta.regions.v2');
    if (cached) { drawRegions(cached); return; }
    var reqs = D.regions.map(function (r) {
      var u = 'https://nominatim.openstreetmap.org/search?format=json&limit=5' +
              '&countrycodes=ru&polygon_geojson=1&polygon_threshold=0.004' +
              '&accept-language=ru&q=' + encodeURIComponent(r.name + ', Россия');
      return fetch(u).then(function (x) { return x.json(); }).catch(function () { return []; });
    });
    Promise.all(reqs).then(function (res) {
      var fc = { type: 'FeatureCollection', features: [] };
      res.forEach(function (arr, i) {
        var hit = (arr || []).filter(function (a) {
          return a.geojson && /Polygon/i.test(a.geojson.type) &&
                 (a.class === 'boundary' || a.addresstype === 'state');
        })[0];
        if (hit) {
          fc.features.push({
            type: 'Feature',
            properties: { name: D.regions[i].name },
            geometry: hit.geojson
          });
        }
      });
      if (!fc.features.length) return;
      cacheSet('karta.regions.v2', fc);
      drawRegions(fc);
    }).catch(function () { /* тихо */ });
  }

  /* ---------------- подписи городов ---------------- */

  function drawCities() {
    if (cityLayer) { maps.main.removeLayer(cityLayer); cityLayer = null; }
    if (!S.showCities) return;
    cityLayer = L.layerGroup().addTo(maps.main);
    D.overview.cities.forEach(function (c) {
      var big = c.rank === 1;
      var html =
        '<div style="display:flex;align-items:center;gap:5px;white-space:nowrap;' +
        'transform:translate(-50%,-50%)">' +
        '<span style="width:' + (big ? 11 : 8) + 'px;height:' + (big ? 11 : 8) + 'px;' +
        'border-radius:50%;background:#f7d64a;border:' + (big ? 2.5 : 2) + 'px solid #3a3a2a;' +
        'display:inline-block;flex:0 0 auto"></span>' +
        '<span style="font:700 ' + (big ? 15 : 12) + 'px Arial,sans-serif;color:#1d2733;' +
        'text-shadow:0 0 4px #fff,0 0 4px #fff,0 0 4px #fff,0 0 4px #fff;' +
        (big ? 'letter-spacing:.06em;text-transform:uppercase' : '') + '">' + c.name + '</span>' +
        '</div>';
      L.marker([c.lat, c.lon], {
        icon: L.divIcon({ className: '', html: html, iconSize: [0, 0] }),
        interactive: false, zIndexOffset: 300
      }).addTo(cityLayer);
    });
  }

  /* ---------------- легенда ---------------- */

  function sym(inner) { return '<span class="sym"><svg viewBox="0 0 46 16" preserveAspectRatio="none">' + inner + '</svg></span>'; }

  function renderLegend() {
    var rows = [];
    rows.push('<h3>Условные обозначения</h3>');

    rows.push('<h4>Объект капитального ремонта</h4>');
    D.objects.forEach(function (o) {
      rows.push('<div class="row">' +
        sym('<circle cx="23" cy="8" r="7" fill="#cc0f24" stroke="#fff" stroke-width="2"/>' +
            '<text x="23" y="11.4" text-anchor="middle" font-size="9" font-weight="700" fill="#fff" font-family="Arial">' + o.n + '</text>') +
        '<span><b>' + o.title + '</b>, ' + o.km + ' — ' + o.region + '</span></div>');
    });
    rows.push('<div class="row">' +
      sym('<line x1="3" y1="8" x2="43" y2="8" stroke="#fff" stroke-width="7" stroke-linecap="round"/>' +
          '<line x1="3" y1="8" x2="43" y2="8" stroke="#cc0f24" stroke-width="4" stroke-linecap="round" stroke-dasharray="7 5"/>') +
      '<span>Место производства работ (искусственное сооружение)</span></div>');
    rows.push('<div class="row">' +
      sym('<circle cx="23" cy="8" r="6.5" fill="none" stroke="#8e1420" stroke-width="2.4"/>' +
          '<line x1="2" y1="8" x2="15" y2="8" stroke="#8e1420" stroke-width="1.6"/>') +
      '<span>Выноска — увеличенный фрагмент карты</span></div>');

    rows.push('<h4>Автомобильные дороги</h4>');
    rows.push('<div class="row">' +
      sym('<line x1="2" y1="8" x2="44" y2="8" stroke="#fff" stroke-width="8" stroke-linecap="round"/>' +
          '<line x1="2" y1="8" x2="44" y2="8" stroke="#cc0f24" stroke-width="3.4" stroke-linecap="round"/>') +
      '<span>М-4 «Дон» — основной ход</span></div>');
    rows.push('<div class="row">' +
      sym('<line x1="2" y1="8" x2="44" y2="8" stroke="#fff" stroke-width="7" stroke-linecap="round"/>' +
          '<line x1="2" y1="8" x2="44" y2="8" stroke="#cc0f24" stroke-width="2.8" stroke-linecap="round" stroke-dasharray="7 5"/>') +
      '<span>М-4 «Дон» — альтернативное направление (проезд по г. Елец)</span></div>');
    rows.push('<div class="row">' +
      sym('<line x1="2" y1="8" x2="44" y2="8" stroke="#8e1420" stroke-width="1.8" stroke-dasharray="7 4"/>') +
      '<span>Границы субъектов Российской Федерации</span></div>');
    rows.push('<div class="row">' +
      sym('<line x1="2" y1="8" x2="44" y2="8" stroke="#3a4450" stroke-width="2"/>' +
          '<line x1="8" y1="4" x2="8" y2="12" stroke="#3a4450" stroke-width="1.4"/>' +
          '<line x1="18" y1="4" x2="18" y2="12" stroke="#3a4450" stroke-width="1.4"/>' +
          '<line x1="28" y1="4" x2="28" y2="12" stroke="#3a4450" stroke-width="1.4"/>' +
          '<line x1="38" y1="4" x2="38" y2="12" stroke="#3a4450" stroke-width="1.4"/>') +
      '<span>Железные дороги, прочие автодороги и населённые пункты — по подложке</span></div>');

    var t = ['<div class="expl"><table><thead><tr>' +
      '<th>№</th><th>Сооружение</th><th>Пикетаж</th><th>Координаты, WGS-84</th><th>Субъект РФ, район</th>' +
      '</tr></thead><tbody>'];
    D.objects.forEach(function (o) {
      t.push('<tr><td class="c">' + o.n + '</td>' +
        '<td>' + o.title + '<br><span style="color:#5a6a79">' + o.sub + '</span></td>' +
        '<td class="c">' + o.km + '</td>' +
        '<td class="c">' + o.lat.toFixed(5) + '<br>' + o.lon.toFixed(5) + '</td>' +
        '<td>' + o.region + '<br><span style="color:#5a6a79">' + o.district + '</span></td></tr>');
    });
    t.push('</tbody></table></div>');
    rows.push(t.join(''));

    $('legend').innerHTML = rows.join('');
  }

  /* ---------------- панель ---------------- */

  function fillBaseSelects() {
    ['c-base-main', 'c-base-inset'].forEach(function (id) {
      var sel = $(id);
      sel.innerHTML = '';
      Object.keys(D.basemaps).forEach(function (k) {
        var op = document.createElement('option');
        op.value = k; op.textContent = D.basemaps[k].label;
        sel.appendChild(op);
      });
    });
    $('c-base-main').value = S.overviewBase;
    $('c-base-inset').value = S.insetBase;
  }

  function syncInputs() {
    D.objects.forEach(function (o, i) {
      var k = 'o' + (i + 1);
      $(k + 'lat').value = o.lat.toFixed(5);
      $(k + 'lon').value = o.lon.toFixed(5);
      $(k + 'z').value = o.inset.zoom;
      $(k + 'ro').textContent = o.lat.toFixed(5) + ', ' + o.lon.toFixed(5) +
        '  (' + o.accuracy + ')';
    });
    renderVerifyLinks();
  }

  function renderVerifyLinks() {
    var box = $('verify-links');
    if (!box) return;
    box.innerHTML = D.objects.map(function (o) {
      return '<div style="margin:5px 0;font-size:11.5px">№' + o.n + ' · ' + o.km + ': ' +
        '<a target="_blank" rel="noopener" href="https://yandex.ru/maps/?ll=' + o.lon + '%2C' + o.lat +
        '&z=17&l=sat%2Cskl&pt=' + o.lon + '%2C' + o.lat + '">Яндекс</a> · ' +
        '<a target="_blank" rel="noopener" href="https://www.openstreetmap.org/?mlat=' + o.lat +
        '&mlon=' + o.lon + '#map=17/' + o.lat + '/' + o.lon + '">OSM</a> · ' +
        '<a target="_blank" rel="noopener" href="https://xn--d1aluo.xn--p1ai/MAP">СКДФ</a></div>';
    }).join('');
  }

  function applyScale() {
    var v = $('c-zoomui').value;
    var sheet = $('sheet');
    var k;
    if (v === 'fit') {
      var avail = $('stage').clientWidth - 52;
      k = Math.min(1, avail / sheet.offsetWidth);
    } else { k = parseFloat(v); }
    $('scaler').style.transform = 'scale(' + k + ')';
    $('scaler').style.height = (sheet.offsetHeight * k) + 'px';
    $('scaler').style.width = (sheet.offsetWidth * k) + 'px';
    setTimeout(function () {
      Object.keys(maps).forEach(function (m) { maps[m].invalidateSize(false); });
      updateLeaders();
    }, 30);
  }

  function applySheet() {
    $('sheet').classList.toggle('a4', S.sheet === 'a4');
    document.body.classList.toggle('a4page', S.sheet === 'a4');
    var st = document.getElementById('pagesize') || (function () {
      var s = document.createElement('style'); s.id = 'pagesize';
      document.head.appendChild(s); return s;
    })();
    st.textContent = '@page { size: ' + (S.sheet === 'a4' ? 'A4' : 'A3') + ' landscape; margin: 0; }';
    buildInsets();
    applyScale();
    setTimeout(function () { fitOverview(); refreshInsets(); }, 60);
  }

  function wire() {
    $('c-sheet').value = S.sheet;
    $('c-tint').checked = S.tint;
    $('c-routes').checked = S.showRoutes;
    $('c-regions').checked = S.showRegions;
    $('c-cities').checked = !!S.showCities;

    $('c-sheet').onchange = function () { S.sheet = this.value; applySheet(); };
    $('c-zoomui').onchange = applyScale;
    $('b-print').onclick = function () { window.print(); };
    $('b-fit').onclick = function () { fitOverview(); };

    $('c-base-main').onchange = function () { S.overviewBase = this.value; setBase('main', this.value); };
    $('c-base-inset').onchange = function () {
      S.insetBase = this.value;
      D.objects.forEach(function (o) { setBase('i' + o.n, S.insetBase); });
    };
    $('c-tint').onchange = function () { $('sheet').classList.toggle('tinted', this.checked); };
    $('c-routes').onchange = function () { S.showRoutes = this.checked; drawRoutes(); };
    $('c-regions').onchange = function () {
      S.showRegions = this.checked;
      if (this.checked) loadRegions(); else drawRegions(null);
    };
    $('c-cities').onchange = function () { S.showCities = this.checked; drawCities(); };

    D.objects.forEach(function (o, i) {
      var k = 'o' + (i + 1);
      function upd() {
        var la = parseFloat($(k + 'lat').value.replace(',', '.'));
        var lo = parseFloat($(k + 'lon').value.replace(',', '.'));
        if (isFinite(la) && isFinite(lo)) {
          o.lat = la; o.lon = lo; o.accuracy = 'задано вручную';
          drawObjects(); refreshInsets(); renderLegend(); syncInputs();
        }
      }
      $(k + 'lat').onchange = upd;
      $(k + 'lon').onchange = upd;
      $(k + 'z').onchange = function () {
        var z = parseInt(this.value, 10);
        if (z >= 9 && z <= 18) { o.inset.zoom = z; refreshInsets(); }
      };
    });

    $('b-reset').onclick = function () {
      location.reload();
    };

    window.addEventListener('resize', applyScale);
    window.addEventListener('beforeprint', function () {
      $('scaler').style.transform = 'none';
      Object.keys(maps).forEach(function (m) { maps[m].invalidateSize(false); });
      updateLeaders();
    });
    window.addEventListener('afterprint', applyScale);
  }

  /* ---------------- старт ---------------- */

  function init() {
    $('t-road').textContent = D.text.road + '.';
    $('t-work').textContent = D.text.work;
    $('t-caption').textContent = D.text.caption;
    $('credits').innerHTML =
      'Подложка: <span id="cr-base"></span>. Геоданные: © OpenStreetMap contributors (ODbL), ' +
      'ГК «Автодор», ФГИС СКДФ. Положение сооружений — по пикетажу М-4 «Дон».';

    $('accuracy-note').innerHTML =
      '<b>Проверьте объект 1.</b> Положение км 398+631 определено интерполяцией ' +
      'пикетажа и соответствует единственному путепроводу через ж.-д. линию на ' +
      'альтернативном направлении юго-восточнее г. Елец. Объект 2 (км 473+479) ' +
      'подтверждён километровыми столбами 473/474 — расхождение ≈ 7 м. ' +
      'Координаты можно править в полях выше или перетаскиванием кружка на карте.';

    fillBaseSelects();
    buildMain();
    buildInsets();
    drawObjects();
    drawCities();
    renderLegend();
    syncInputs();
    wire();
    applySheet();
    loadRoutes();
    if (S.showRegions) loadRegions();

    var upd = function () { var e = $('cr-base'); if (e) e.textContent = D.basemaps[S.overviewBase].attribution; };
    upd();
    $('c-base-main').addEventListener('change', upd);

    setTimeout(updateLeaders, 400);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
