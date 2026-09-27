export interface BuiltinTemplate {
  id: string
  name: string
  description: string
  mermaid: string
}

export const BUILTIN_TEMPLATES: BuiltinTemplate[] = [
  {
    id: 'microservices',
    name: 'Microserviços',
    description: 'Serviços independentes com API Gateway, mensageria e banco por serviço',
    mermaid: `graph TB
  Client-->Gateway[API Gateway]
  Gateway-->Auth[Auth Service]
  Gateway-->Order[Order Service]
  Gateway-->Product[Product Service]
  Order-->OrderDB[(Orders DB)]
  Product-->ProductDB[(Products DB)]
  Order-->Queue[Message Queue]
  Queue-->Notify[Notification Service]`,
  },
  {
    id: 'clean-arch',
    name: 'Clean Architecture',
    description: 'Camadas: domain, use cases, adapters e frameworks',
    mermaid: `graph TB
  Framework[Frameworks & Drivers]-->Adapters[Interface Adapters]
  Adapters-->Usecases[Application Use Cases]
  Usecases-->Domain[Domain / Entities]
  style Domain fill:#10b981,color:#fff
  style Usecases fill:#6366f1,color:#fff
  style Adapters fill:#f59e0b,color:#fff
  style Framework fill:#ef4444,color:#fff`,
  },
  {
    id: 'cqrs',
    name: 'CQRS + Event Sourcing',
    description: 'Separação de comandos e queries com event store',
    mermaid: `graph LR
  Client-->|Command|CommandBus[Command Bus]
  Client-->|Query|QueryBus[Query Bus]
  CommandBus-->Handler[Command Handler]
  Handler-->EventStore[(Event Store)]
  EventStore-->Projector[Projector]
  Projector-->ReadModel[(Read Model)]
  QueryBus-->ReadModel`,
  },
  {
    id: 'k8s',
    name: 'Kubernetes Cluster',
    description: 'Estrutura básica de cluster com pods, services e ingress',
    mermaid: `graph TB
  Internet-->Ingress[Ingress Controller]
  Ingress-->SvcA[Service A]
  Ingress-->SvcB[Service B]
  SvcA-->PodA1[Pod A1]
  SvcA-->PodA2[Pod A2]
  SvcB-->PodB1[Pod B1]
  PodA1-->DB[(Database)]
  PodA2-->DB`,
  },
  {
    id: 'saga',
    name: 'Saga Pattern',
    description: 'Orquestração de transações distribuídas com compensação',
    mermaid: `sequenceDiagram
  participant O as Order Service
  participant P as Payment Service
  participant I as Inventory Service
  participant N as Notification
  O->>P: Reserve Payment
  P-->>O: Payment Reserved
  O->>I: Reserve Stock
  I-->>O: Stock Reserved
  O->>P: Confirm Payment
  O->>I: Confirm Stock
  O->>N: Send Confirmation`,
  },
]
