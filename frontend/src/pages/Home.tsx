import { useEffect } from 'react'

import AppLayout from '../components/layout/AppLayout'
import { useAppStore } from '../store/useAppStore'

export default function Home() {
  const closeDiagram = useAppStore((state) => state.closeDiagram)

  useEffect(() => {
    closeDiagram()
  }, [closeDiagram])

  return <AppLayout />
}
