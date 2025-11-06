import { useEffect, useState } from 'react'
import './heart-trail.style.css'
interface Heart {
  id: number
  x: number
  y: number
}

export default function HeartTrail() {
  const [hearts, setHearts] = useState<Heart[]>([])

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const newHeart: Heart = {
        id: Date.now(),
        x: e.clientX,
        y: e.clientY
      }

      setHearts((prev) => [...prev, newHeart])

      // Remove after 1s
      setTimeout(() => {
        setHearts((prev) => prev.filter((heart) => heart.id !== newHeart.id))
      }, 1000)
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  return (
    <div>
      {hearts.map((heart) => (
        <span key={heart.id} className='heart' style={{ left: heart.x, top: heart.y }}>
          ❤️
        </span>
      ))}
    </div>
  )
}
