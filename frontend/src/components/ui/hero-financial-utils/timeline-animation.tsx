'use client'
import React from 'react'
import { motion, useInView, Variant } from 'framer-motion'

interface TimelineAnimationProps extends React.HTMLAttributes<HTMLElement> {
  children?: React.ReactNode
  timelineRef: React.RefObject<HTMLDivElement | null>
  animationNum: number
  className?: string
  as?: any
  // allow img attrs
  src?: string
  alt?: string
}

const HIDDEN: Variant = { opacity: 0, y: 24, filter: 'blur(4px)' }
const VISIBLE: Variant = { opacity: 1, y: 0, filter: 'blur(0px)' }

export function TimelineAnimation({
  children,
  timelineRef,
  animationNum,
  className,
  as = 'div',
  ...rest
}: TimelineAnimationProps) {
  const isInView = useInView(timelineRef, { once: true, amount: 0.05 })

  // motion[tag] needs to be constructed dynamically
  const MotionTag = motion[as as 'div'] as React.ElementType

  return (
    <MotionTag
      className={className}
      initial={HIDDEN}
      animate={isInView ? VISIBLE : HIDDEN}
      transition={{
        delay: animationNum * 0.12,
        duration: 0.55,
        ease: [0.22, 1, 0.36, 1],
      }}
      {...rest}
    >
      {children}
    </MotionTag>
  )
}
