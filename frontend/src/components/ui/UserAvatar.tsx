import { useState, type CSSProperties } from 'react'

import { initial } from '../../utils/format'

interface UserAvatarProps {
  name: string
  pictureUrl?: string | null
  className: string
  style?: CSSProperties
}

// The identity provider's photo when there is one and it loads; the name's initial otherwise.
export default function UserAvatar({ name, pictureUrl, className, style }: UserAvatarProps) {
  const [failedUrl, setFailedUrl] = useState<string | null>(null)
  const hasPicture = typeof pictureUrl === 'string' && pictureUrl !== '' && pictureUrl !== failedUrl
  if (!hasPicture) {
    return (
      <span className={className} style={style} aria-hidden>
        {initial(name)}
      </span>
    )
  }
  return (
    <img
      className={className}
      style={style}
      src={pictureUrl}
      alt=""
      // Google photo URLs refuse requests that carry our page as the referrer.
      referrerPolicy="no-referrer"
      onError={() => setFailedUrl(pictureUrl)}
    />
  )
}
