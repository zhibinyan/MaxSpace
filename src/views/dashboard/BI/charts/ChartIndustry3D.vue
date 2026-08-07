<template>
  <div ref="el" class="chart3d"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'

const el = ref(null)
let renderer, scene, camera, group, animId, ro

const nodes = [
  { name: '工业', value: 1.2, color: 0x38bdf8 },
  { name: '农业', value: 0.85, color: 0x34d399 },
  { name: '服务业', value: 1.05, color: 0xfbbf24 },
  { name: '科技', value: 0.95, color: 0xa78bfa },
  { name: '金融', value: 0.75, color: 0x22d3ee },
]

const build = () => {
  if (!el.value) return
  const w = el.value.clientWidth || 280
  const h = el.value.clientHeight || 180

  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(40, w / h, 0.1, 100)
  camera.position.set(0, -6.5, 5.5)
  camera.lookAt(0, 0, 0)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setSize(w, h)
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2))
  el.value.innerHTML = ''
  el.value.appendChild(renderer.domElement)

  scene.add(new THREE.AmbientLight(0xffffff, 0.75))
  const light = new THREE.DirectionalLight(0xffffff, 1.1)
  light.position.set(4, -3, 8)
  scene.add(light)

  group = new THREE.Group()
  scene.add(group)

  // 中心球体
  const core = new THREE.Mesh(
    new THREE.SphereGeometry(0.85, 32, 32),
    new THREE.MeshPhysicalMaterial({
      color: 0x0ea5e9,
      metalness: 0.3,
      roughness: 0.25,
      emissive: 0x0284c7,
      emissiveIntensity: 0.35,
      clearcoat: 0.8,
    }),
  )
  group.add(core)

  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(1.55, 0.035, 12, 64),
    new THREE.MeshBasicMaterial({ color: 0x3de7ff, transparent: true, opacity: 0.55 }),
  )
  ring.rotation.x = Math.PI / 2.4
  group.add(ring)

  nodes.forEach((n, i) => {
    const a = (i / nodes.length) * Math.PI * 2
    const r = 2.2
    const mesh = new THREE.Mesh(
      new THREE.SphereGeometry(0.28 * n.value, 24, 24),
      new THREE.MeshPhysicalMaterial({
        color: n.color,
        metalness: 0.2,
        roughness: 0.3,
        emissive: n.color,
        emissiveIntensity: 0.25,
      }),
    )
    mesh.position.set(Math.cos(a) * r, Math.sin(a) * r, Math.sin(a * 2) * 0.35)
    mesh.userData.base = mesh.position.clone()
    mesh.userData.phase = i
    group.add(mesh)

    const lineGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, 0),
      mesh.position.clone(),
    ])
    group.add(new THREE.Line(
      lineGeo,
      new THREE.LineBasicMaterial({ color: n.color, transparent: true, opacity: 0.45 }),
    ))
  })

  // 中心数值标签用 CSS overlay 更清晰，这里用 sprite 简化
  const canvas = document.createElement('canvas')
  canvas.width = 256
  canvas.height = 128
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#7ef0ff'
  ctx.font = 'bold 42px sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('38374', 128, 58)
  ctx.font = '22px sans-serif'
  ctx.fillStyle = 'rgba(180,220,255,0.85)'
  ctx.fillText('总产值(亿)', 128, 95)
  const tex = new THREE.CanvasTexture(canvas)
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }))
  sprite.scale.set(2.2, 1.1, 1)
  sprite.position.set(0, 0, 1.4)
  group.add(sprite)

  const animate = () => {
    animId = requestAnimationFrame(animate)
    const t = performance.now() * 0.001
    group.rotation.z = t * 0.15
    group.children.forEach((c) => {
      if (c.userData?.base) {
        c.position.z = c.userData.base.z + Math.sin(t * 2 + c.userData.phase) * 0.12
      }
    })
    renderer.render(scene, camera)
  }
  animate()
}

const onResize = () => {
  if (!el.value || !renderer || !camera) return
  const w = el.value.clientWidth
  const h = el.value.clientHeight
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h)
}

onMounted(() => {
  build()
  ro = new ResizeObserver(onResize)
  ro.observe(el.value)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animId)
  ro?.disconnect()
  renderer?.dispose()
  renderer?.domElement?.remove()
})
</script>

<style scoped>
.chart3d {
  width: 100%;
  height: 100%;
  min-height: 120px;
}
.chart3d :deep(canvas) {
  display: block;
  width: 100% !important;
  height: 100% !important;
}
</style>
