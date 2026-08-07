import { md5 } from 'js-md5'

/** MD5 hex digest (32 chars, lowercase). */
export function md5Hash(text: string): string {
  return md5(text)
}
