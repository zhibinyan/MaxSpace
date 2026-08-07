<template>
  <div class="cockpit">
    <button
      v-if="activeRegion"
      class="back-btn"
      type="button"
      @click="backToNational"
    >
      ← 返回全国
    </button>

    <div ref="mapWrapper" class="map-viewport"></div>

    <aside class="legend-panel">
      <label
        v-for="item in legendItems"
        :key="item.key"
        class="legend-item"
        :class="{ active: toggles[item.key] }"
      >
        <input
          v-model="toggles[item.key]"
          type="checkbox"
          @change="onToggle(item.key)"
        />
        <i :class="['dot', item.key]" />
        <span>{{ item.label }}</span>
      </label>
    </aside>

    <div class="hint-tip">点击省份或标签可下钻 · 如福建</div>
    <div v-if="loading" class="loading-mask">地图数据加载中...</div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { CSS3DRenderer, CSS3DSprite } from 'three/examples/jsm/renderers/CSS3DRenderer.js'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'

const mapWrapper = ref(null)
const loading = ref(true)
const activeRegion = ref(null) // { name, adcode } | null

const toggles = reactive({
  flyline: true,
  hotspot: true,
  scatter: true,
  particles: true,
})

const legendItems = [
  { key: 'flyline', label: '路径飞线' },
  { key: 'hotspot', label: '重点监控' },
  { key: 'scatter', label: '地图点位' },
  { key: 'particles', label: '上升粒子' },
]

const MAP_SCALE = 0.28
const EXTRUDE_BASE = 0.8

/** 省名 → 行政区划代码（用于下钻加载市级 GeoJSON） */
const provinceAdcodes = {
  北京: '110000', 天津: '120000', 河北: '130000', 山西: '140000', 内蒙古: '150000',
  辽宁: '210000', 吉林: '220000', 黑龙江: '230000',
  上海: '310000', 江苏: '320000', 浙江: '330000', 安徽: '340000', 福建: '350000',
  江西: '360000', 山东: '370000',
  河南: '410000', 湖北: '420000', 湖南: '430000', 广东: '440000', 广西: '450000', 海南: '460000',
  重庆: '500000', 四川: '510000', 贵州: '520000', 云南: '530000', 西藏: '540000',
  陕西: '610000', 甘肃: '620000', 青海: '630000', 宁夏: '640000', 新疆: '650000',
  台湾: '710000', 香港: '810000', 澳门: '820000',
}

const provinceCenters = {
  北京: [116.4, 39.9], 天津: [117.2, 39.1], 上海: [121.5, 31.2], 重庆: [106.5, 29.6],
  河北: [114.5, 38.0], 山西: [112.5, 37.9], 辽宁: [123.4, 41.8], 吉林: [125.3, 43.9],
  黑龙江: [126.6, 45.8], 江苏: [119.8, 33.0], 浙江: [120.2, 30.3], 安徽: [117.3, 31.8],
  福建: [119.3, 26.1], 江西: [115.9, 27.6], 山东: [120.0, 36.4], 河南: [113.7, 33.9],
  湖北: [112.4, 30.6], 湖南: [112.0, 27.1], 广东: [113.3, 23.1], 海南: [110.0, 19.2],
  四川: [102.2, 30.6], 贵州: [106.7, 26.6], 云南: [102.7, 25.0], 西藏: [89.1, 31.5],
  陕西: [109.0, 35.0], 甘肃: [103.8, 36.0], 青海: [96.0, 36.0], 宁夏: [106.3, 37.5],
  新疆: [85.6, 42.1], 台湾: [121.0, 24.0], 香港: [114.2, 22.3], 澳门: [113.5, 22.2],
  内蒙古: [111.8, 43.8], 广西: [108.4, 23.5],
}

const provinceData = {
  北京市: 78, 天津市: 64, 上海市: 82, 重庆市: 55,
  河北省: 48, 山西省: 42, 辽宁省: 51, 吉林省: 38,
  黑龙江省: 35, 江苏省: 88, 浙江省: 79, 安徽省: 52,
  福建省: 61, 江西省: 44, 山东省: 76, 河南省: 58,
  湖北省: 63, 湖南省: 57, 广东省: 92, 海南省: 41,
  四川省: 68, 贵州省: 39, 云南省: 43, 西藏自治区: 22,
  陕西省: 54, 甘肃省: 31, 青海省: 18, 宁夏回族自治区: 28,
  新疆维吾尔自治区: 33, 台湾省: 70, 香港特别行政区: 85,
  澳门特别行政区: 72, 内蒙古自治区: 36, 广西壮族自治区: 47,
}

const nameMapping = {
  北京市: '北京', 天津市: '天津', 上海市: '上海', 重庆市: '重庆',
  河北省: '河北', 山西省: '山西', 辽宁省: '辽宁', 吉林省: '吉林',
  黑龙江省: '黑龙江', 江苏省: '江苏', 浙江省: '浙江', 安徽省: '安徽',
  福建省: '福建', 江西省: '江西', 山东省: '山东', 河南省: '河南',
  湖北省: '湖北', 湖南省: '湖南', 广东省: '广东', 海南省: '海南',
  四川省: '四川', 贵州省: '贵州', 云南省: '云南', 西藏自治区: '西藏',
  陕西省: '陕西', 甘肃省: '甘肃', 青海省: '青海', 宁夏回族自治区: '宁夏',
  新疆维吾尔自治区: '新疆', 台湾省: '台湾', 香港特别行政区: '香港',
  澳门特别行政区: '澳门', 内蒙古自治区: '内蒙古', 广西壮族自治区: '广西',
}

/** 飞线路径：从中心向外辐射 */
const flyRoutes = [
  ['北京', '上海'], ['北京', '广东'], ['北京', '四川'], ['北京', '新疆'],
  ['北京', '黑龙江'], ['北京', '云南'], ['上海', '广东'], ['广东', '四川'],
  ['江苏', '四川'], ['浙江', '湖北'], ['山东', '新疆'], ['河南', '广东'],
]

let scene, camera, renderer, css3dRenderer, composer, controls
let mapGroup, labelGroup, flylineGroup, hotspotGroup, scatterGroup, particleSystem
let clock, animId, nationalGeoJSON
let raycaster, pointer
let pointerDownPos = null
const flylineUniforms = []

/** 投影参数（下钻时会改中心与缩放） */
const proj = { lng: 105, lat: 35, scale: MAP_SCALE }

const projection = (lng, lat) => {
  const x = (lng - proj.lng) * 2.0 * proj.scale
  const y = (lat - proj.lat) * 2.2 * proj.scale
  return [x, y]
}

const shortName = (full) =>
  nameMapping[full] || full.replace(/[省市区壮回族维吾尔特别行政自治区]/g, '')

const getValue = (full, short) =>
  provinceData[full] ?? provinceData[`${short}省`] ?? provinceData[`${short}市`] ?? 40

const loadGeoJSON = async (adcode = '100000') => {
  const urls = [
    `https://geo.datav.aliyun.com/areas_v3/bound/${adcode}_full.json`,
    `https://geo.datav.aliyun.com/areas_v3/bound/${adcode}.json`,
  ]
  for (const url of urls) {
    try {
      const res = await fetch(url)
      if (res.ok) return await res.json()
    } catch (_) { /* try next */ }
  }
  throw new Error(`GeoJSON 加载失败: ${adcode}`)
}

/** 计算 GeoJSON feature 中心点 */
const featureCenter = (feature) => {
  let sumLng = 0
  let sumLat = 0
  let n = 0
  const walk = (coords) => {
    if (!Array.isArray(coords)) return
    if (typeof coords[0] === 'number') {
      sumLng += coords[0]
      sumLat += coords[1]
      n++
      return
    }
    coords.forEach(walk)
  }
  walk(feature.geometry?.coordinates)
  return n ? [sumLng / n, sumLat / n] : null
}

/** 根据 GeoJSON 计算包围盒，更新投影中心与缩放 */
const fitProjection = (geojson, padding = 1.15) => {
  let minLng = Infinity
  let maxLng = -Infinity
  let minLat = Infinity
  let maxLat = -Infinity
  const walk = (coords) => {
    if (!Array.isArray(coords)) return
    if (typeof coords[0] === 'number') {
      minLng = Math.min(minLng, coords[0])
      maxLng = Math.max(maxLng, coords[0])
      minLat = Math.min(minLat, coords[1])
      maxLat = Math.max(maxLat, coords[1])
      return
    }
    coords.forEach(walk)
  }
  geojson.features.forEach((f) => walk(f.geometry?.coordinates))
  proj.lng = (minLng + maxLng) / 2
  proj.lat = (minLat + maxLat) / 2
  const spanLng = Math.max(maxLng - minLng, 0.5)
  const spanLat = Math.max(maxLat - minLat, 0.5)
  // 目标世界尺寸约 28，按较大边缩放
  const target = 28
  const scaleLng = target / (spanLng * 2.0)
  const scaleLat = target / (spanLat * 2.2)
  proj.scale = Math.min(scaleLng, scaleLat) * padding
}

const createProvinceMaterial = (value) => {
  const t = Math.min(value / 100, 1)
  const color = new THREE.Color().setHSL(0.55 - t * 0.08, 0.75, 0.18 + t * 0.22)
  return new THREE.MeshPhysicalMaterial({
    color,
    transparent: true,
    opacity: 0.88,
    metalness: 0.2,
    roughness: 0.35,
    clearcoat: 0.6,
    clearcoatRoughness: 0.2,
    emissive: color.clone().multiplyScalar(0.35),
    emissiveIntensity: 0.4,
    side: THREE.DoubleSide,
  })
}

const createProvinceMesh = (feature, value, meta = {}) => {
  const group = new THREE.Object3D()
  const coords = feature.geometry.coordinates
  const depth = EXTRUDE_BASE + (value / 100) * 1.6

  const processPolygon = (ring) => {
    if (!ring || ring.length < 3) return
    const shape = new THREE.Shape()
    ring.forEach((pt, i) => {
      if (!pt || pt.length < 2) return
      const [x, y] = projection(pt[0], pt[1])
      if (i === 0) shape.moveTo(x, y)
      else shape.lineTo(x, y)
    })

    try {
      const geo = new THREE.ExtrudeGeometry(shape, {
        depth,
        bevelEnabled: true,
        bevelThickness: 0.08,
        bevelSize: 0.06,
        bevelSegments: 2,
      })
      const mesh = new THREE.Mesh(geo, createProvinceMaterial(value))
      mesh.userData = { ...meta, clickable: true }
      group.add(mesh)

      const edges = new THREE.LineSegments(
        new THREE.EdgesGeometry(geo, 20),
        new THREE.LineBasicMaterial({
          color: 0x6ee7ff,
          transparent: true,
          opacity: 0.7,
        }),
      )
      group.add(edges)
    } catch (e) {
      console.warn('province mesh failed', e)
    }
  }

  if (feature.geometry.type === 'MultiPolygon') {
    coords.forEach((multi) => multi.forEach((poly) => processPolygon(poly)))
  } else if (feature.geometry.type === 'Polygon') {
    coords.forEach((poly) => processPolygon(poly))
  }

  group.userData = { ...meta, depth, clickable: true }
  return group
}

/** CSS3D 标签：小胶囊，置于光柱/散点/粒子之上；可点击下钻 */
const createCSS3DLabel = (name, lng, lat, value, meta = {}) => {
  const [x, y] = projection(lng, lat)
  const pillarH = 2 + (value / 100) * 6
  const el = document.createElement('div')
  el.className = 'css3d-label'
  el.innerHTML = `
    <span class="label-value">${value}%</span>
    <span class="label-sep"></span>
    <span class="label-name">${name}</span>
  `

  const adcode = meta.adcode || provinceAdcodes[name] || ''
  const canDrill = Boolean(adcode) && meta.level !== 'city'

  if (canDrill) {
    el.classList.add('is-clickable')
    el.title = `点击进入${name}`
    el.addEventListener('pointerdown', (e) => {
      e.stopPropagation()
    })
    el.addEventListener('click', (e) => {
      e.stopPropagation()
      e.preventDefault()
      if (activeRegion.value) return
      drillToProvince(name, adcode)
    })
  }

  const sprite = new CSS3DSprite(el)
  sprite.scale.set(0.022, 0.022, 0.022)
  sprite.position.set(x, y, EXTRUDE_BASE + pillarH + 1.2)
  sprite.userData = { name, adcode, clickable: canDrill }
  return sprite
}

/** 飞线：贝塞尔弧 + 流光 Shader */
const createFlyline = (from, to) => {
  const [x1, y1] = projection(from[0], from[1])
  const [x2, y2] = projection(to[0], to[1])
  const midX = (x1 + x2) / 2
  const midY = (y1 + y2) / 2
  const dist = Math.hypot(x2 - x1, y2 - y1)
  const height = Math.max(3.5, dist * 0.5)

  const curve = new THREE.QuadraticBezierCurve3(
    new THREE.Vector3(x1, y1, EXTRUDE_BASE + 0.35),
    new THREE.Vector3(midX, midY, EXTRUDE_BASE + height),
    new THREE.Vector3(x2, y2, EXTRUDE_BASE + 0.35),
  )

  const uniforms = {
    uTime: { value: 0 },
    uColor: { value: new THREE.Color(0x4df5ff) },
    uSpeed: { value: 0.55 + Math.random() * 0.45 },
  }
  flylineUniforms.push(uniforms)

  const tubeGeo = new THREE.TubeGeometry(curve, 64, 0.06, 8, false)
  // 沿管线写入进度属性
  const posCount = tubeGeo.attributes.position.count
  const progress = new Float32Array(posCount)
  const radial = tubeGeo.parameters.radialSegments + 1
  const tubular = tubeGeo.parameters.tubularSegments
  for (let i = 0; i <= tubular; i++) {
    for (let j = 0; j < radial; j++) {
      progress[i * radial + j] = i / tubular
    }
  }
  tubeGeo.setAttribute('aProgress', new THREE.BufferAttribute(progress, 1))

  const mat = new THREE.ShaderMaterial({
    uniforms,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    vertexShader: `
      attribute float aProgress;
      varying float vProgress;
      void main() {
        vProgress = aProgress;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uTime;
      uniform vec3 uColor;
      uniform float uSpeed;
      varying float vProgress;
      void main() {
        float head = fract(uTime * uSpeed);
        float d = fract(vProgress - head + 1.0);
        float trail = 1.0 - smoothstep(0.0, 0.28, d);
        float base = 0.15;
        float alpha = base + trail * trail * 0.95;
        vec3 col = mix(uColor * 0.45, vec3(1.0), trail * 0.7);
        gl_FragColor = vec4(col, alpha);
      }
    `,
  })

  const g = new THREE.Group()
  g.add(new THREE.Mesh(tubeGeo, mat))

  // 端点光斑
  ;[[x1, y1], [x2, y2]].forEach(([x, y]) => {
    const dot = new THREE.Mesh(
      new THREE.SphereGeometry(0.18, 12, 12),
      new THREE.MeshBasicMaterial({
        color: 0x7ef8ff,
        transparent: true,
        opacity: 0.9,
      }),
    )
    dot.position.set(x, y, EXTRUDE_BASE + 0.4)
    g.add(dot)
  })

  return g
}

/** 光柱 */
const createLightPillar = (lng, lat, value) => {
  const [x, y] = projection(lng, lat)
  const h = 2 + (value / 100) * 6
  const geo = new THREE.CylinderGeometry(0.08, 0.18, h, 16, 1, true)
  geo.translate(0, h / 2, 0)
  const mat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    uniforms: {
      uColor: { value: new THREE.Color(0x4df0ff) },
    },
    vertexShader: `
      varying float vY;
      void main() {
        vY = position.y;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform vec3 uColor;
      varying float vY;
      void main() {
        float a = smoothstep(0.0, 1.5, vY) * (1.0 - smoothstep(2.0, 8.0, vY));
        gl_FragColor = vec4(uColor, a * 0.55);
      }
    `,
  })
  const mesh = new THREE.Mesh(geo, mat)
  mesh.rotation.x = Math.PI / 2
  mesh.position.set(x, y, EXTRUDE_BASE + 0.2)
  return mesh
}

/** 散点 */
const createScatterPoints = (centers) => {
  const positions = []
  Object.values(centers).forEach(([lng, lat]) => {
    const [x, y] = projection(lng, lat)
    positions.push(x, y, EXTRUDE_BASE + 0.35)
  })
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  const mat = new THREE.PointsMaterial({
    color: 0x7ef0ff,
    size: 0.35,
    transparent: true,
    opacity: 0.9,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  })
  return new THREE.Points(geo, mat)
}

/** 上升粒子 */
const createRisingParticles = () => {
  const count = 400
  const positions = new Float32Array(count * 3)
  const speeds = new Float32Array(count)
  for (let i = 0; i < count; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 40
    positions[i * 3 + 1] = (Math.random() - 0.5) * 35
    positions[i * 3 + 2] = Math.random() * 8
    speeds[i] = 0.4 + Math.random() * 1.2
  }
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geo.setAttribute('aSpeed', new THREE.BufferAttribute(speeds, 1))
  const mat = new THREE.PointsMaterial({
    color: 0x66e0ff,
    size: 0.12,
    transparent: true,
    opacity: 0.55,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  })
  const points = new THREE.Points(geo, mat)
  points.userData.speeds = speeds
  return points
}

/** 地面网格 + 涟漪 */
const createFloor = () => {
  const group = new THREE.Group()

  const grid = new THREE.GridHelper(60, 40, 0x1a4a7a, 0x12355a)
  grid.rotation.x = Math.PI / 2
  grid.position.z = -0.2
  grid.material.transparent = true
  grid.material.opacity = 0.35
  group.add(grid)

  for (let i = 1; i <= 4; i++) {
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(i * 4.5, i * 4.5 + 0.06, 64),
      new THREE.MeshBasicMaterial({
        color: 0x2ec8ff,
        transparent: true,
        opacity: 0.25 / i,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    )
    ring.position.z = -0.1
    group.add(ring)
  }

  return group
}

const onToggle = (key) => {
  const map = {
    flyline: flylineGroup,
    hotspot: hotspotGroup,
    scatter: scatterGroup,
    particles: particleSystem,
  }
  const obj = map[key]
  if (obj) obj.visible = toggles[key]
}

const disposeObject = (obj) => {
  obj.traverse((child) => {
    if (child.geometry) child.geometry.dispose()
    if (child.material) {
      if (Array.isArray(child.material)) child.material.forEach((m) => m.dispose())
      else child.material.dispose()
    }
    if (child.element?.parentNode) child.element.remove()
  })
}

const clearMapLayers = () => {
  ;[mapGroup, labelGroup, flylineGroup, hotspotGroup, scatterGroup, particleSystem].forEach((g) => {
    if (!g) return
    disposeObject(g)
    scene.remove(g)
  })
  flylineUniforms.length = 0
  mapGroup = labelGroup = flylineGroup = hotspotGroup = scatterGroup = particleSystem = null
}

/** 构建全国地图 */
const buildNationalMap = (geojson) => {
  proj.lng = 105
  proj.lat = 35
  proj.scale = MAP_SCALE

  mapGroup = new THREE.Group()
  labelGroup = new THREE.Group()
  flylineGroup = new THREE.Group()
  hotspotGroup = new THREE.Group()
  const centersUsed = {}

  geojson.features.forEach((feature) => {
    if (!feature.geometry || !feature.properties) return
    const full = feature.properties.name || feature.properties.NAME || ''
    if (!full) return
    const short = shortName(full)
    const value = getValue(full, short)
    const adcode = provinceAdcodes[short] || String(feature.properties.adcode || '')

    const province = createProvinceMesh(feature, value, {
      name: short,
      fullName: full,
      adcode,
      level: 'province',
    })
    if (province.children.length) mapGroup.add(province)

    const center = provinceCenters[short]
    if (center) {
      centersUsed[short] = center
      if (value >= 60) {
        hotspotGroup.add(createLightPillar(center[0], center[1], value))
        labelGroup.add(
          createCSS3DLabel(short, center[0], center[1], value, {
            adcode,
            level: 'province',
          }),
        )
      }
    }
  })

  flyRoutes.forEach(([a, b]) => {
    const from = provinceCenters[a]
    const to = provinceCenters[b]
    if (from && to) flylineGroup.add(createFlyline(from, to))
  })

  scatterGroup = createScatterPoints(centersUsed)
  particleSystem = createRisingParticles()
  mapGroup.rotation.x = 0.08

  ;[mapGroup, flylineGroup, hotspotGroup, scatterGroup, particleSystem, labelGroup].forEach(
    (g) => {
      if (!g) return
      if (g === flylineGroup) g.visible = toggles.flyline
      else if (g === hotspotGroup) g.visible = toggles.hotspot
      else if (g === scatterGroup) g.visible = toggles.scatter
      else if (g === particleSystem) g.visible = toggles.particles
      scene.add(g)
    },
  )
}

/** 构建省内市级地图 */
const buildProvinceMap = (geojson, provinceName) => {
  fitProjection(geojson, 1.05)

  mapGroup = new THREE.Group()
  labelGroup = new THREE.Group()
  flylineGroup = new THREE.Group()
  hotspotGroup = new THREE.Group()
  const centersUsed = {}
  const cityList = []

  geojson.features.forEach((feature, idx) => {
    if (!feature.geometry || !feature.properties) return
    const full = feature.properties.name || feature.properties.NAME || `区域${idx + 1}`
    const short = full.replace(/[市县区]/g, '') || full
    const value = 35 + ((idx * 17) % 55)
    const center = featureCenter(feature)
    if (!center) return

    const mesh = createProvinceMesh(feature, value, {
      name: short,
      fullName: full,
      adcode: String(feature.properties.adcode || ''),
      level: 'city',
      parent: provinceName,
    })
    if (mesh.children.length) mapGroup.add(mesh)

    centersUsed[short] = center
    cityList.push({ name: short, center, value })
  })

  // 省内飞线：连接前几个城市
  for (let i = 0; i < Math.min(cityList.length - 1, 5); i++) {
    flylineGroup.add(createFlyline(cityList[i].center, cityList[i + 1].center))
  }
  if (cityList.length > 2) {
    flylineGroup.add(createFlyline(cityList[0].center, cityList[cityList.length - 1].center))
  }

  cityList.forEach(({ name, center, value }) => {
    if (value >= 50) {
      hotspotGroup.add(createLightPillar(center[0], center[1], value))
      labelGroup.add(createCSS3DLabel(name, center[0], center[1], value))
    }
  })

  scatterGroup = createScatterPoints(centersUsed)
  particleSystem = createRisingParticles()
  mapGroup.rotation.x = 0.08

  ;[mapGroup, flylineGroup, hotspotGroup, scatterGroup, particleSystem, labelGroup].forEach(
    (g) => {
      if (!g) return
      if (g === flylineGroup) g.visible = toggles.flyline
      else if (g === hotspotGroup) g.visible = toggles.hotspot
      else if (g === scatterGroup) g.visible = toggles.scatter
      else if (g === particleSystem) g.visible = toggles.particles
      scene.add(g)
    },
  )
}

const drillToProvince = async (name, adcode) => {
  if (!adcode) return
  loading.value = true
  try {
    const geojson = await loadGeoJSON(adcode)
    clearMapLayers()
    activeRegion.value = { name, adcode }
    buildProvinceMap(geojson, name)
    // 拉近一点看省地图
    camera.up.set(0, 0, 1)
    camera.position.set(0, -55, 28)
    controls.target.set(0, 0, 2)
    controls.update()
  } catch (e) {
    console.error('下钻失败', e)
  } finally {
    loading.value = false
  }
}

const backToNational = async () => {
  if (!nationalGeoJSON) return
  loading.value = true
  try {
    clearMapLayers()
    activeRegion.value = null
    buildNationalMap(nationalGeoJSON)
    camera.up.set(0, 0, 1)
    camera.position.set(0, -36, 48)
    controls.target.set(0, 0, 2)
    controls.update()
  } finally {
    loading.value = false
  }
}

const findClickable = (obj) => {
  let cur = obj
  while (cur) {
    if (cur.userData?.clickable && cur.userData?.name) return cur.userData
    cur = cur.parent
  }
  return null
}

const onPointerDown = (event) => {
  pointerDownPos = { x: event.clientX, y: event.clientY }
}

const onPointerMove = (event) => {
  if (!mapWrapper.value || !mapGroup) return
  const rect = mapWrapper.value.getBoundingClientRect()
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
  raycaster.setFromCamera(pointer, camera)
  const hits = raycaster.intersectObjects(mapGroup.children, true)
  const meta = hits.length ? findClickable(hits[0].object) : null
  mapWrapper.value.style.cursor =
    meta && !activeRegion.value && provinceAdcodes[meta.name] ? 'pointer' : 'default'
}

const onPointerClick = (event) => {
  if (!mapWrapper.value || !mapGroup || activeRegion.value) return
  if (pointerDownPos) {
    const dx = event.clientX - pointerDownPos.x
    const dy = event.clientY - pointerDownPos.y
    if (dx * dx + dy * dy > 25) return // 拖拽不触发下钻
  }

  const rect = mapWrapper.value.getBoundingClientRect()
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
  raycaster.setFromCamera(pointer, camera)
  const hits = raycaster.intersectObjects(mapGroup.children, true)
  if (!hits.length) return

  const meta = findClickable(hits[0].object)
  if (!meta?.name) return
  const adcode = meta.adcode || provinceAdcodes[meta.name]
  if (adcode) drillToProvince(meta.name, adcode)
}

const onResize = () => {
  if (!mapWrapper.value || !camera || !renderer) return
  const w = mapWrapper.value.clientWidth
  const h = mapWrapper.value.clientHeight
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h)
  css3dRenderer.setSize(w, h)
  composer?.setSize(w, h)
}

const animate = () => {
  animId = requestAnimationFrame(animate)
  const t = clock.getElapsedTime()

  controls?.update()

  flylineUniforms.forEach((u) => {
    u.uTime.value = t
  })

  if (particleSystem?.visible) {
    const pos = particleSystem.geometry.attributes.position
    const speeds = particleSystem.userData.speeds
    for (let i = 0; i < speeds.length; i++) {
      pos.array[i * 3 + 2] += speeds[i] * 0.02
      if (pos.array[i * 3 + 2] > 10) pos.array[i * 3 + 2] = 0
    }
    pos.needsUpdate = true
  }

  composer?.render()
  css3dRenderer?.render(scene, camera)
}

const initScene = async () => {
  const el = mapWrapper.value
  const w = el.clientWidth
  const h = el.clientHeight

  scene = new THREE.Scene()
  scene.fog = new THREE.FogExp2(0x061428, 0.012)

  camera = new THREE.PerspectiveCamera(42, w / h, 0.1, 300)
  // 地图挤出沿 Z 轴，相机以 Z 为“上”，拖拽上滑才是俯仰
  camera.up.set(0, 0, 1)
  camera.position.set(0, -36, 48)
  camera.lookAt(0, 0, 2)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setSize(w, h)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setClearColor(0x061428, 1)
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.15
  el.appendChild(renderer.domElement)

  css3dRenderer = new CSS3DRenderer()
  css3dRenderer.setSize(w, h)
  css3dRenderer.domElement.className = 'css3d-layer'
  el.appendChild(css3dRenderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.06
  controls.target.set(0, 0, 2)
  controls.minDistance = 18
  controls.maxDistance = 100
  // 允许按住左键往上滑：靠近俯视；往下滑：接近平视
  controls.minPolarAngle = 0.2
  controls.maxPolarAngle = Math.PI * 0.48
  controls.enableRotate = true
  controls.rotateSpeed = 0.65
  controls.screenSpacePanning = true
  controls.mouseButtons = {
    LEFT: THREE.MOUSE.ROTATE,
    MIDDLE: THREE.MOUSE.DOLLY,
    RIGHT: THREE.MOUSE.PAN,
  }

  raycaster = new THREE.Raycaster()
  pointer = new THREE.Vector2()

  scene.add(new THREE.AmbientLight(0x4a6aaa, 0.85))
  const key = new THREE.DirectionalLight(0xffffff, 1.6)
  key.position.set(12, 28, 24)
  scene.add(key)
  const fill = new THREE.DirectionalLight(0x3a8cff, 0.55)
  fill.position.set(-16, -8, 10)
  scene.add(fill)

  scene.add(createFloor())

  nationalGeoJSON = await loadGeoJSON('100000')
  buildNationalMap(nationalGeoJSON)

  const bloom = new UnrealBloomPass(new THREE.Vector2(w, h), 0.45, 0.35, 0.82)
  composer = new EffectComposer(renderer)
  composer.addPass(new RenderPass(scene, camera))
  composer.addPass(bloom)
  composer.addPass(new OutputPass())

  clock = new THREE.Clock()
  loading.value = false
  window.addEventListener('resize', onResize)
  el.addEventListener('pointermove', onPointerMove)
  el.addEventListener('pointerdown', onPointerDown)
  el.addEventListener('click', onPointerClick)
  animate()
}

onMounted(() => {
  initScene().catch((e) => {
    console.error(e)
    loading.value = false
  })
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animId)
  window.removeEventListener('resize', onResize)
  mapWrapper.value?.removeEventListener('pointermove', onPointerMove)
  mapWrapper.value?.removeEventListener('pointerdown', onPointerDown)
  mapWrapper.value?.removeEventListener('click', onPointerClick)
  controls?.dispose()
  composer?.dispose()
  renderer?.dispose()
  css3dRenderer?.domElement.remove()
  renderer?.domElement.remove()
})
</script>

<style>
html,
body,
#app {
  margin: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #061428;
  font-family: 'DIN Alternate', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.cockpit {
  position: relative;
  width: 100%;
  height: 100%;
  background:
    radial-gradient(ellipse 80% 60% at 50% 45%, #0a2a4a 0%, transparent 55%),
    linear-gradient(180deg, #04101f 0%, #061428 40%, #030b18 100%);
}

.map-viewport {
  position: absolute;
  inset: 0;
}

.map-viewport canvas {
  display: block;
}

.css3d-layer {
  position: absolute !important;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

/* CSS3D 小胶囊标签 */
.css3d-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 22px;
  padding: 0 10px;
  white-space: nowrap;
  color: #fff;
  font-size: 11px;
  line-height: 1;
  background: linear-gradient(180deg, rgba(12, 48, 82, 0.92), rgba(6, 28, 56, 0.9));
  border: 1px solid rgba(90, 210, 255, 0.7);
  border-radius: 999px;
  box-shadow:
    0 0 10px rgba(40, 180, 255, 0.35),
    inset 0 0 8px rgba(40, 160, 255, 0.1);
  backdrop-filter: blur(4px);
  transform: translate(-50%, -50%);
  user-select: none;
  pointer-events: none;
}

.css3d-label.is-clickable {
  pointer-events: auto;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.css3d-label.is-clickable:hover {
  border-color: #7ef0ff;
  box-shadow:
    0 0 16px rgba(80, 220, 255, 0.55),
    inset 0 0 10px rgba(40, 160, 255, 0.18);
  transform: translate(-50%, -50%) scale(1.08);
}

.css3d-label .label-value {
  font-size: 11px;
  font-weight: 700;
  color: #7ef0ff;
  text-shadow: 0 0 6px rgba(80, 220, 255, 0.7);
}

.css3d-label .label-sep {
  width: 1px;
  height: 10px;
  background: rgba(90, 210, 255, 0.45);
}

.css3d-label .label-name {
  font-size: 10px;
  letter-spacing: 0.06em;
  color: rgba(230, 245, 255, 0.92);
}

.legend-panel {
  position: absolute;
  left: 50%;
  bottom: 88px;
  z-index: 30;
  display: flex;
  flex-direction: row;
  gap: 14px;
  padding: 10px 16px;
  transform: translateX(-50%);
  background: rgba(6, 24, 48, 0.55);
  border: 1px solid rgba(50, 150, 220, 0.35);
  backdrop-filter: blur(8px);
}

.hint-tip {
  position: absolute;
  left: 50%;
transform: translateX(-50%);
  bottom: 70px;
  z-index: 30;
  color: rgba(160, 210, 240, 0.45);
  font-size: 12px;
  letter-spacing: 0.12em;
  pointer-events: none;
}

.back-btn {
  position: absolute;
  top: 108px;
  left: 50%;
  z-index: 35;
  padding: 8px 16px;
  color: #c8eaff;
  font-size: 13px;
  letter-spacing: 0.08em;
  cursor: pointer;
  transform: translateX(-50%);
  background: rgba(6, 28, 52, 0.75);
  border: 1px solid rgba(70, 190, 255, 0.55);
  backdrop-filter: blur(6px);
  transition: all 0.2s;
}
.back-btn:hover {
  color: #fff;
  border-color: #7ef0ff;
  box-shadow: 0 0 14px rgba(60, 200, 255, 0.35);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: rgba(180, 210, 230, 0.55);
  font-size: 13px;
  letter-spacing: 0.08em;
  transition: color 0.2s;
}
.legend-item.active {
  color: #c8eaff;
}
.legend-item input {
  display: none;
}
.legend-item .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 1px solid rgba(100, 200, 255, 0.5);
  background: transparent;
  box-shadow: none;
  transition: all 0.2s;
}
.legend-item.active .dot {
  background: #3de7ff;
  box-shadow: 0 0 10px #3de7ff;
}
.legend-item.active .dot.hotspot { background: #5b8cff; box-shadow: 0 0 10px #5b8cff; }
.legend-item.active .dot.scatter { background: #7ef0ff; box-shadow: 0 0 10px #7ef0ff; }
.legend-item.active .dot.particles { background: #9ae8ff; box-shadow: 0 0 10px #9ae8ff; }

.loading-mask {
  position: absolute;
  inset: 0;
  z-index: 40;
  display: grid;
  place-items: center;
  background: rgba(4, 14, 28, 0.75);
  color: #7ee8ff;
  letter-spacing: 0.2em;
  font-size: 14px;
}

@media (max-width: 768px) {
  .legend-panel {
    left: 12px;
    bottom: 16px;
    padding: 10px 12px;
    transform: none;
  }
}
</style>
