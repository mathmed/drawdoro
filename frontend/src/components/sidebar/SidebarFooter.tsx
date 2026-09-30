import { KeyRound, LogOut, Monitor, Moon, Sparkles, Sun } from 'lucide-react'
import { useState, type ReactNode } from 'react'

import { logout } from '../../auth/session'
import { useAuthStore } from '../../store/useAuthStore'
import { useThemeStore, type ThemePreference } from '../../store/useThemeStore'
import ApiKeysDialog from '../account/ApiKeysDialog'
import ConnectClaudeDialog from '../account/ConnectClaudeDialog'
import Logo from '../ui/Logo'
import Menu from '../ui/Menu'
import UserAvatar from '../ui/UserAvatar'

const THEME_OPTIONS: { value: ThemePreference; icon: ReactNode; label: string }[] = [
  { value: 'light', icon: <Sun size={14} />, label: 'Light' },
  { value: 'dark', icon: <Moon size={14} />, label: 'Dark' },
  { value: 'system', icon: <Monitor size={14} />, label: 'System' },
]

export default function SidebarFooter() {
  const profile = useAuthStore((state) => state.profile)
  const themePreference = useThemeStore((state) => state.preference)
  const setThemePreference = useThemeStore((state) => state.setPreference)
  const [accountDialog, setAccountDialog] = useState<'connect' | 'keys' | null>(null)

  return (
    <div className="sidebar-footer">
      {accountDialog === 'connect' ? <ConnectClaudeDialog onClose={() => setAccountDialog(null)} /> : null}
      {accountDialog === 'keys' ? <ApiKeysDialog onClose={() => setAccountDialog(null)} /> : null}
      {profile !== null ? (
        <Menu
          side="top"
          className="menu-anchor user-anchor"
          items={[
            { kind: 'label', label: profile.email },
            { label: 'Connect Claude', icon: <Sparkles size={15} />, onSelect: () => setAccountDialog('connect') },
            { label: 'API keys', icon: <KeyRound size={15} />, onSelect: () => setAccountDialog('keys') },
            { label: 'Sign out', icon: <LogOut size={15} />, onSelect: logout },
          ]}
          trigger={({ toggle }) => (
            <button type="button" className="user-button" onClick={toggle} title={profile.email}>
              <UserAvatar className="user-avatar" name={profile.name} pictureUrl={profile.picture} />
              <span className="user-name">{profile.name}</span>
            </button>
          )}
        />
      ) : (
        <Logo size={20} withWordmark />
      )}
      <div className="segmented" role="group" aria-label="Theme">
        {THEME_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            aria-label={option.label}
            aria-pressed={themePreference === option.value}
            title={option.label}
            onClick={() => setThemePreference(option.value)}
          >
            {option.icon}
          </button>
        ))}
      </div>
    </div>
  )
}
