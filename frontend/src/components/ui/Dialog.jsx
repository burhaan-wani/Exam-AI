import { useState } from 'react'
import { X } from 'lucide-react'

const Dialog = ({ open, onOpenChange, children }) => {
  return (
    <>
      {open && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
            {children}
          </div>
        </div>
      )}
    </>
  )
}

const DialogContent = ({ children, onClose }) => (
  <div className="relative">
    <button
      onClick={onClose}
      className="absolute top-4 right-4 p-1 hover:bg-gray-100 rounded-lg"
    >
      <X size={20} />
    </button>
    <div className="p-6">{children}</div>
  </div>
)

const DialogHeader = ({ children }) => (
  <div className="flex flex-col space-y-2 text-center border-b p-6 pb-4">
    {children}
  </div>
)

const DialogTitle = ({ children }) => (
  <h2 className="text-lg font-semibold leading-none tracking-tight">
    {children}
  </h2>
)

const DialogDescription = ({ children }) => (
  <p className="text-sm text-gray-600">{children}</p>
)

const DialogFooter = ({ children }) => (
  <div className="flex justify-end gap-2 p-6 border-t">{children}</div>
)

export { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter }
