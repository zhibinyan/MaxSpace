export interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'editor' | 'viewer'
  status: 'active' | 'disabled'
  createdAt: string
}

export interface MenuItem {
  path: string
  title: string
  icon: string
}
