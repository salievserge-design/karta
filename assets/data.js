/* ------------------------------------------------------------------
   Карта объекта — исходные данные
   Правьте этот файл, чтобы изменить подписи, координаты и вид листа.
   ------------------------------------------------------------------ */

window.KARTA = {

  /* ---------- Текстовая часть листа ---------- */
  text: {
    road:
      'Автомобильная дорога М-4 «Дон» Москва – Воронеж – Ростов-на-Дону – ' +
      'Краснодар – Новороссийск',
    work:
      'Капитальный ремонт путепровода через ж/д на км 398+631 ' +
      '(альтернативное направление, проезд по г. Елец) Липецкая область ' +
      'и путепровода через а/д на км 473+479 Воронежская область',
    caption: 'Рисунок 1 – Схема расположения объекта'
  },

  /* ---------- Сооружения ---------- */
  objects: [
    {
      n: 1,
      title: 'Путепровод через ж/д',
      km: 'км 398+631',
      sub: 'альтернативное направление, проезд по г. Елец',
      region: 'Липецкая область',
      district: 'Елецкий муниципальный округ',
      /* Положение получено интерполяцией пикетажа М-4 «Дон» и проверено
         по OSM: единственный путепровод через ж.-д. линию Юго-Восточной
         ж.д. на альтернативном направлении юго-восточнее г. Елец.
         ТОЧНОСТЬ: ориентировочная, уточните по ведомости ИССО. */
      lat: 52.56352,
      lon: 38.67952,
      accuracy: 'ориентировочно',
      axis: 123,          // азимут оси сооружения, ° (для знака «участок работ»)
      inset: { zoom: 14, place: 'top' },
      insetCaption: 'Выноска 1 · путепровод через ж/д, км 398+631'
    },
    {
      n: 2,
      title: 'Путепровод через а/д',
      km: 'км 473+479',
      sub: 'основной ход М-4 «Дон»',
      region: 'Воронежская область',
      district: 'Рамонский район, Комсомольское с/п',
      /* Положение получено интерполяцией между километровыми столбами
         км 473 и км 474 (OSM highway=milestone) и совпало с существующим
         путепроводом (way 34626100) с точностью ≈ 7 м. */
      lat: 52.00772,
      lon: 39.21242,
      accuracy: 'по километровым столбам',
      axis: 69,
      inset: { zoom: 14, place: 'bottom' },
      insetCaption: 'Выноска 2 · путепровод через а/д, км 473+479'
    }
  ],

  /* ---------- Обзорная карта ---------- */
  overview: {
    bounds: [[51.58, 38.05], [52.98, 39.95]],
    paddingTopLeft: [46, 124],
    paddingBottomRight: [520, 150],
    cities: [
      { name: 'Липецк',   lat: 52.6031, lon: 39.5708, rank: 1 },
      { name: 'Воронеж',  lat: 51.6720, lon: 39.1843, rank: 1 },
      { name: 'Елец',     lat: 52.6170, lon: 38.5060, rank: 2 },
      { name: 'Задонск',  lat: 52.3960, lon: 38.9270, rank: 3 },
      { name: 'Рамонь',   lat: 51.9130, lon: 39.3400, rank: 3 },
      { name: 'Хлевное',  lat: 52.1930, lon: 39.1060, rank: 3 }
    ]
  },

  /* ---------- Трассы (encoded polyline, OSRM) ---------- */
  routes: {
    /* Основной ход М-4 «Дон» на участке Елец — Воронеж (генерализовано).
       При наличии сети уточняется «на лету» через OSRM. */
    main: '}wzaI_abiFd|FzhG_nBnpEqcLz`Gdc@~qCnpEqUnzGymMz_Jk~@vuL}ef@zgKabMjdCkaNjkIqiCtxMa|NvfMatDpnAkdFfaI_yIhuKia_@hyMytDveD{eNl|EuvG~jGon@zvFznCxqW{cHf~W|v@jvKclOxhHsnAf{E|r@jzD`{H`sG`iE',
    /* Альтернативное направление (проезд по г. Елец) на участке
       севернее Ельца — примыкание к основному ходу. */
    alt: 'epq`I}rviFvCa`@tVeUtEoi@yPatAdo@gf@xxBkZb{@eb@|vBFhAh]vfAtOH_t@yD|EfAs^lSqiA~t@tZvDmeA{KszAxaDo|PziBqtGhs@weCnaAitB}IsHkS`V',

    /* Запросы для уточнения геометрии в браузере пользователя */
    osrmMain: 'https://router.project-osrm.org/route/v1/driving/38.3500,52.9000;39.2200,51.6200?overview=full&geometries=polyline&steps=false&alternatives=false',
    osrmAlt:  'https://router.project-osrm.org/route/v1/driving/38.4600,52.6900;38.5060,52.6170;38.6795,52.5635;38.7177,52.5495?overview=full&geometries=polyline&steps=false&alternatives=false'
  },

  /* ---------- Границы субъектов (подгружаются и кэшируются) ---------- */
  regions: [
    { name: 'Липецкая область',    osm: 'R115051' },
    { name: 'Воронежская область', osm: 'R72181'  }
  ],

  /* ---------- Подложки ---------- */
  basemaps: {
    esriTopo: {
      label: 'Атлас (Esri Topo) — ближе всего к СКДФ',
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
      maxZoom: 19,
      attribution: 'Esri, HERE, Garmin, FAO, NOAA, USGS, © OpenStreetMap contributors'
    },
    openTopo: {
      label: 'OpenTopoMap (рельеф, горизонтали)',
      url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
      subdomains: 'abc',
      maxZoom: 17,
      attribution: '© OpenTopoMap, © OpenStreetMap contributors (ODbL)'
    },
    osm: {
      label: 'OpenStreetMap (стандарт)',
      url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors (ODbL)'
    },
    voyager: {
      label: 'CartoDB Voyager (светлая)',
      url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
      subdomains: 'abcd',
      maxZoom: 20,
      attribution: '© OpenStreetMap contributors, © CARTO'
    },
    esriImagery: {
      label: 'Космоснимок (Esri)',
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      maxZoom: 19,
      attribution: 'Esri, Maxar, Earthstar Geographics'
    }
  },

  defaults: {
    sheet: 'a3',
    overviewBase: 'esriTopo',
    insetBase: 'esriTopo',
    tint: true,
    showRoutes: true,
    showRegions: true,
    showCities: true
  }
};
