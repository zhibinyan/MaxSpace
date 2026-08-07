export type MaxAlign = 'left' | 'center' | 'right'

export interface MaxColumn<T = Record<string, unknown>> {
  /** 字段 key，对应 row 上的属性 */
  key: keyof T & string
  /** 表头文案 */
  label: string
  /** 列宽，如 80 / '120px' / '1fr' */
  width?: string | number
  minWidth?: string | number
  align?: MaxAlign
  /** 额外 class */
  className?: string
}

export interface MaxRowContext<T> {
  row: T
  index: number
}

export interface MaxCellContext<T> extends MaxRowContext<T> {
  column: MaxColumn<T>
  value: unknown
}
