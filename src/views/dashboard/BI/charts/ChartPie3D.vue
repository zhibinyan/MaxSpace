<template>
  <div ref="el" class="chart3d"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as THREE from 'three'

const props = defineProps({
  data: {
    type: Array,
    default: () => [
      { name: '第一产业', value: 28, color: '#3b82f6' },
      { name: '第二产业', value: 35, color: '#22d3ee' },
      { name: '第三产业', value: 22, color: '#fbbf24' },
      { name: '新兴产业', value: 15, color: '#34d399' },
    ],
  },
})

const el = ref(null)
let renderer, scene, camera, group, animId, ro

const build = () => {
  if (!el.value) return
  const w = el.value.clientWidth || 280
  const h = el.value.clientHeight || 180

  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(35, w / h, 0.1, 100)
  camera.position.set(0, -7.5, 6.2)
  camera.lookAt(0, 0, 0.4)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setSize(w, h)
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2))
  el.value.innerHTML = ''
  el.value.appendChild(renderer.domElement)

  scene.add(new THREE.AmbientLight(0xffffff, 0.7))
  const key = new THREE.DirectionalLight(0xffffff, 1.2)
  key.position.set(3, -4, 8)
  scene.add(key)

  group = new THREE.Group()
  scene.add(group)

  const total = props.data.reduce((s, d) => s + d.value, 0) || 1
  let start = -Math.PI / 2
  const inner = 0.9
  const outer = 2.2

  props.data.forEach((item, idx) => {
    const angle = (item.value / total) * Math.PI * 2
    const depth = 0.35 + (item.value / total) * 1.1
    const shape = new THREE.Shape()
    const segments = Math.max(12, Math.ceil(angle * 24))

    for (let i = 0; i <= segments; i++) {
      const a = start + (angle * i) / segments
      const x = Math.cos(a) * outer
      const y = Math.sin(a) * outer
      if (i === 0) shape.moveTo(x, y)
      else shape.lineTo(x, y)
    }
    for (let i = segments; i >= 0; i--) {
      const a = start + (angle * i) / segments
      shape.lineTo(Math.cos(a) * inner, Math.sin(a) * inner)
    }
    shape.closePath()

    const geo = new THREE.ExtrudeGeometry(shape, {
      depth,
      bevelEnabled: true,
      bevelThickness: 0.06,
      bevelSize: 0.04,
      bevelSegments: 2,
    })
    const mat = new THREE.MeshPhysicalMaterial({
      color: new THREE.Color(item.color),
      metalness: 0.25,
      roughness: 0.35,
      clearcoat: 0.6,
      emissive: new THREE.Color(item.color),
      emissiveIntensity: 0.2,
    })
    const mesh = new THREE.Mesh(geo, mat)
    mesh.position.z = idx * 0.02
    group.add(mesh)
    start += angle
  })

  // 底座环
  const base = new THREE.Mesh(
    new THREE.RingGeometry(inner - 0.05, outer + 0.15, 64),
    new THREE.MeshBasicMaterial({
      color: 0x1a4a7a,
      transparent: true,
      opacity: 0.35,
      side: THREE.DoubleSide,
    }),
  )
  base.position.z = -0.05
  group.add(base)

  const animate = () => {
    animId = requestAnimationFrame(animate)
    group.rotation.z += 0.004
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

const dispose = () => {
  cancelAnimationFrame(animId)
  ro?.disconnect()
  if (group) {
    group.traverse((o) => {
      o.geometry?.dispose()
      if (o.material) {
        if (Array.isArray(o.material)) o.material.forEach((m) => m.dispose())
        else o.material.dispose()
      }
    })
  }
  renderer?.dispose()
  renderer?.domElement?.remove()
}

onMounted(() => {
  build()
  ro = new ResizeObserver(onResize)
  ro.observe(el.value)
})

watch(() => props.data, () => {
  dispose()
  build()
  ro = new ResizeObserver(onResize)
  if (el.value) ro.observe(el.value)
}, { deep: true })

onBeforeUnmount(dispose)
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
