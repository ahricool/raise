const A_STOCK_RE = /^\d{6}$/
const A_STOCK_PREFIX_RE = /^(SH|SZ)\d{6}$/i
const HK_STOCK_RE = /^(hk)?\d{5}$/i
const US_STOCK_RE = /^[A-Za-z]{1,6}(\.[A-Za-z]{1,2})?$/

export function validateStockCode(value: string): string | null {
  const v = value.trim().toUpperCase()
  if (!v) return '请输入股票代码'
  if (
    A_STOCK_RE.test(v) ||
    A_STOCK_PREFIX_RE.test(v) ||
    HK_STOCK_RE.test(v) ||
    US_STOCK_RE.test(v)
  ) {
    return null
  }
  return '股票代码格式不正确'
}
