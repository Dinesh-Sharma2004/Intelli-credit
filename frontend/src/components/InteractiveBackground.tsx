import React, { useEffect, useRef, useState, useCallback } from 'react'

interface MousePosition {
  x: number
  y: number
}

interface ClickRipple {
  id: number
  x: number
  y: number
  timestamp: number
}

export const InteractiveBackground = React.memo(() => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationRef = useRef<number>()
  const mousePosition = useRef<MousePosition>({ x: 0, y: 0 })
  const [clickRipples, setClickRipples] = useState<ClickRipple[]>([])
  const rippleIdRef = useRef(0)

  const handleMouseMove = useCallback((e: MouseEvent) => {
    mousePosition.current = { x: e.clientX, y: e.clientY }
  }, [])

  const handleClick = useCallback((e: MouseEvent) => {
    const newRipple: ClickRipple = {
      id: rippleIdRef.current++,
      x: e.clientX,
      y: e.clientY,
      timestamp: Date.now()
    }

    setClickRipples(prev => [...prev, newRipple])

    setTimeout(() => {
      setClickRipples(prev => prev.filter(r => r.id !== newRipple.id))
    }, 2000)
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const resizeCanvas = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }

    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('click', handleClick)

    let time = 0

    const animate = () => {
      if (!ctx) return

      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const gradient1 = ctx.createRadialGradient(
        canvas.width * 0.3 + Math.sin(time * 0.0005) * 100,
        canvas.height * 0.3 + Math.cos(time * 0.0007) * 100,
        0,
        canvas.width * 0.3,
        canvas.height * 0.3,
        canvas.width * 0.4
      )

      const gradient2 = ctx.createRadialGradient(
        canvas.width * 0.7 + Math.cos(time * 0.0006) * 150,
        canvas.height * 0.7 + Math.sin(time * 0.0008) * 150,
        0,
        canvas.width * 0.7,
        canvas.height * 0.7,
        canvas.width * 0.3
      )

      const mouseGradient = ctx.createRadialGradient(
        mousePosition.current.x,
        mousePosition.current.y,
        0,
        mousePosition.current.x,
        mousePosition.current.y,
        300
      )

      const isDark = document.documentElement.classList.contains('dark')

      if (isDark) {
        gradient1.addColorStop(0, 'rgba(59, 130, 246, 0.15)')
        gradient1.addColorStop(0.5, 'rgba(147, 51, 234, 0.1)')
        gradient1.addColorStop(1, 'transparent')

        gradient2.addColorStop(0, 'rgba(236, 72, 153, 0.12)')
        gradient2.addColorStop(0.5, 'rgba(34, 211, 238, 0.08)')
        gradient2.addColorStop(1, 'transparent')

        mouseGradient.addColorStop(0, 'rgba(99, 102, 241, 0.2)')
        mouseGradient.addColorStop(0.5, 'rgba(168, 85, 247, 0.1)')
        mouseGradient.addColorStop(1, 'transparent')
      } else {
        gradient1.addColorStop(0, 'rgba(59, 130, 246, 0.08)')
        gradient1.addColorStop(0.5, 'rgba(147, 51, 234, 0.05)')
        gradient1.addColorStop(1, 'transparent')

        gradient2.addColorStop(0, 'rgba(236, 72, 153, 0.06)')
        gradient2.addColorStop(0.5, 'rgba(34, 211, 238, 0.04)')
        gradient2.addColorStop(1, 'transparent')

        mouseGradient.addColorStop(0, 'rgba(99, 102, 241, 0.1)')
        mouseGradient.addColorStop(0.5, 'rgba(168, 85, 247, 0.05)')
        mouseGradient.addColorStop(1, 'transparent')
      }

      ctx.fillStyle = gradient1
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      ctx.fillStyle = gradient2
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      ctx.fillStyle = mouseGradient
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      const now = Date.now()

      clickRipples.forEach(ripple => {
        const age = (now - ripple.timestamp) / 2000

        if (age <= 1) {
          const radius = age * 200
          const opacity = 1 - age

          const rippleGradient = ctx.createRadialGradient(
            ripple.x,
            ripple.y,
            0,
            ripple.x,
            ripple.y,
            radius
          )

          if (isDark) {
            rippleGradient.addColorStop(0, `rgba(147,197,253,${opacity * 0.3})`)
            rippleGradient.addColorStop(0.5, `rgba(196,181,253,${opacity * 0.2})`)
            rippleGradient.addColorStop(1, 'transparent')
          } else {
            rippleGradient.addColorStop(0, `rgba(59,130,246,${opacity * 0.2})`)
            rippleGradient.addColorStop(0.5, `rgba(147,51,234,${opacity * 0.1})`)
            rippleGradient.addColorStop(1, 'transparent')
          }

          ctx.fillStyle = rippleGradient
          ctx.fillRect(0, 0, canvas.width, canvas.height)
        }
      })

      time += 16
      animationRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      window.removeEventListener('resize', resizeCanvas)
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('click', handleClick)

      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [handleMouseMove, handleClick, clickRipples])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0"
      style={{ opacity: 0.7 }}
    />
  )
})