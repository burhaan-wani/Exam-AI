import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

const Button = forwardRef(
  (
    {
      className,
      variant = 'default',
      size = 'md',
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'inline-flex items-center justify-center rounded-xl font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed'

    const variants = {
      default:
        'bg-slate-900 text-white hover:bg-slate-800 active:bg-slate-900',
      secondary:
        'bg-gray-200 text-gray-900 hover:bg-gray-300 active:bg-gray-200',
      outline:
        'border border-gray-300 text-gray-900 hover:bg-gray-50 active:bg-white',
      ghost:
        'text-gray-900 hover:bg-gray-100 active:bg-white',
      destructive:
        'bg-red-600 text-white hover:bg-red-700 active:bg-red-600',
    }

    const sizes = {
      sm: 'h-8 px-3 text-sm',
      md: 'h-10 px-4 text-sm',
      lg: 'h-11 px-5 text-base',
    }

    return (
      <button
        className={cn(
          baseStyles,
          variants[variant],
          sizes[size],
          className
        )}
        disabled={disabled}
        ref={ref}
        {...props}
      >
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'

export default Button
