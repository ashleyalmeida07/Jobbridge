'use client'
import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X } from 'lucide-react'

interface MotionDrawerProps {
  children: React.ReactNode
  direction?: 'left' | 'right'
  width?: number
  backgroundColor?: string
  clsBtnClassName?: string
  contentClassName?: string
  btnClassName?: string
}

export default function MotionDrawer({
  children,
  direction = 'left',
  width = 300,
  backgroundColor = '#ffffff',
  clsBtnClassName = '',
  contentClassName = '',
  btnClassName = '',
}: MotionDrawerProps) {
  const [open, setOpen] = useState(false)
  const drawerRef = useRef<HTMLDivElement>(null)

  // Close on ESC
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [])

  // Lock body scroll
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  const xFrom = direction === 'left' ? -width : width

  return (
    <>
      {/* Trigger button */}
      <button
        className={`z-50 ${btnClassName}`}
        aria-label="Open menu"
        onClick={() => setOpen(true)}
      >
        <Menu size={20} />
      </button>

      <AnimatePresence>
        {open && (
          <>
            {/* Backdrop */}
            <motion.div
              key="backdrop"
              className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
            />

            {/* Drawer panel */}
            <motion.div
              key="drawer"
              ref={drawerRef}
              className={`fixed top-0 ${direction === 'left' ? 'left-0' : 'right-0'} h-full z-50 flex flex-col ${contentClassName}`}
              style={{ width, backgroundColor }}
              initial={{ x: xFrom }}
              animate={{ x: 0 }}
              exit={{ x: xFrom }}
              transition={{ type: 'spring', stiffness: 340, damping: 38 }}
            >
              {/* Close button */}
              <button
                className={`absolute top-3 ${direction === 'left' ? 'right-3' : 'left-3'} p-2 rounded-lg transition ${clsBtnClassName}`}
                aria-label="Close menu"
                onClick={() => setOpen(false)}
              >
                <X size={18} />
              </button>

              {/* Content */}
              <div className="p-6 pt-14 flex-1 overflow-y-auto">
                {children}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}
