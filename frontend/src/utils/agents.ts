export interface AgentIdentity {
  name: string
  ownerName?: string | null
  label?: string | null
}

// "Ana's Claude": agents with a personal key are named after their owner, so two people's
// agents never look alike. Agents on the shared service key have no owner.
export function agentDisplayName({ name, ownerName }: AgentIdentity): string {
  return ownerName ? `${ownerName}'s ${name}` : name
}

export function agentDescription(agent: AgentIdentity): string {
  const label = agent.label ? ` · ${agent.label}` : ''
  return `${agentDisplayName(agent)} (AI agent${label})`
}
