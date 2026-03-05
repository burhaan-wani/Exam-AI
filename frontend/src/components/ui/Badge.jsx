import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

const Badge = forwardRef(({ className, variant = 'default', ...props }, ref) => {
  const variants = {
    default: 'bg-slate-900 text-white',
    secondary: 'bg-gray-200 text-gray-900',
    destructive: 'bg-red-100 text-red-900',
    success: 'bg-green-100 text-green-900',
    warning: 'bg-yellow-100 text-yellow-900',
    outline: 'border border-gray-300 text-gray-900',
  }

  return (
    <div
      ref={ref}
      className={cn(
        'inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold',
        variants[variant],
        className
      )}
      {...props}
    />
  )
})
Badge.displayName = 'Badge'

export default Badge
