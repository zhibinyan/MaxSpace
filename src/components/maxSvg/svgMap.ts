const svgModules = import.meta.glob<string>('@/assets/svg/**/*.svg', {
  eager: true,
  import: 'default',
})

function toSvgKey(path: string): string {
  const marker = '/assets/svg/'
  const index = path.lastIndexOf(marker)
  if (index === -1) {
    return path.split('/').pop()?.replace(/\.svg$/, '') ?? ''
  }
  return path.slice(index + marker.length).replace(/\.svg$/, '')
}

export const svgMap = Object.fromEntries(
  Object.entries(svgModules).map(([path, url]) => [toSvgKey(path), url]),
) as Record<string, string>

export const svgNames = Object.keys(svgMap).sort((a, b) =>
  a.localeCompare(b, 'zh-CN'),
)

export function resolveSvgByName(name: string): string | undefined {
  return svgMap[name]
}
