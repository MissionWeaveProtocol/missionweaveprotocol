# MissionWeaveProtocol

This context defines the language for organization-internal Missions completed by
coordinator-led groups of autonomous Agents.

## Protocol identity

**MissionWeaveProtocol**:
The canonical organization-internal cooperation protocol for autonomous Agents working in
Mission Groups.
_Avoid_: Abbreviated, spaced, or alternate product names

## Organization and identity

**Organization**:
The trusted governance root that registers Agents, defines policy, and authenticates humans.
_Avoid_: Network, federation

**Agent**:
A single independently scheduled runtime with one stable identity and at most one active session.
_Avoid_: Service, replica, process pool

**Agent Card**:
An organization-signed description of an Agent's stable identity and verified capabilities.
_Avoid_: Profile, presence

**Agent Registry**:
The Organization-controlled source of current Agent Cards, signing keys, capability evidence, and
their validity status.
_Avoid_: Presence service, peer discovery

**Principal**:
An authenticated Agent, human, or Organization service that can be named as the actor or owner of
a protocol object.
_Avoid_: Display name, unauthenticated user

**Presence Record**:
Ephemeral information about an Agent's availability, capacity, and recent heartbeat.
_Avoid_: Agent Card

**Capability**:
A versioned, organization-governed kind of work an Agent is verified to perform.
_Avoid_: Permission, free-form skill

**Group Authority**:
Organization infrastructure that authenticates actors, validates policy and Membership, serializes
Group transitions, and appends Events without acting as the Mission's semantic manager.
_Avoid_: Coordinator, consensus protocol

**Authorization Service**:
The Organization service that evaluates execution policy and issues short-lived scoped capability
tokens after assignment, lease, budget, and approval checks succeed.
_Avoid_: Agent Registry, Scheduler

**Capability Token**:
A short-lived execution grant bound to one Worker session, WorkItem, Ownership Epoch, Execution
Lease, allowed operations and resources, and bounded budgets.
_Avoid_: Capability, reusable credential

**Membership Token**:
A short-lived authorization bound to one Principal, Group, Membership Epoch, Session Epoch, and
least-privilege role set.
_Avoid_: Capability Token, subscription

## Mission collaboration

**Mission**:
A bounded objective with a definition of done, budget, deadline, and approval lifecycle.
_Avoid_: Project, task

**Child Mission**:
A Mission created to complete one complex WorkItem of a parent Mission.
_Avoid_: Subtask

**Follow-up Mission**:
A new Mission linked to an immutable approved Mission when later correction or additional work is
required.
_Avoid_: Editing an approved Mission

**Group**:
The temporary collaboration space and shared history belonging to exactly one Mission.
_Avoid_: Channel, room, team

**MissionOwner**:
A Mission's accountable principal. A root MissionOwner is human and holds final approval,
cancellation, and Coordinator-replacement authority. A child MissionOwner is the parent
Coordinator and approves the child result on behalf of its parent WorkItem; organization risk
policy may additionally require direct human approval.
_Avoid_: User, administrator

**Coordinator**:
The replaceable Agent responsible for planning, assignment, monitoring, integration, and submission.
_Avoid_: POC Agent, manager service, sequencer

**Worker**:
An Agent that accepts and executes WorkItems using its own queues and Scheduler.
_Avoid_: Sub-agent, tool

**Membership**:
The scoped authorization connecting an Agent or MissionOwner to one Group.
_Avoid_: Subscription, presence

**Work Delegate**:
A Group member eligible to authorize narrowly scoped WorkItems through an explicit Delegation
Grant; the role itself grants no work-authoring authority.
_Avoid_: Coordinator, unrestricted administrator

**Delegation Grant**:
An authoritative, non-transferable authorization from the current Coordinator to one Work
Delegate for one target WorkItem subtree, bounded by capability versions, cumulative Resource
Budget, descendant depth, expiry, and Membership and Coordinator Epochs. It ends when its target
becomes terminal.
_Avoid_: Role name alone, transferable credential

## Conversation and work

**Conversation**:
An auditable thread of Messages scoped to a Group or one WorkItem.
_Avoid_: Session, chat log

**Message**:
Committed conversational context that never grants executable authority by itself.
_Avoid_: Command, instruction

**WorkItem**:
An explicit unit of Mission work with an owner, lifecycle, dependencies, and Work Contract.
_Avoid_: Message, Mission, job

**Work Proposal**:
A non-executable request by any Group member to create a WorkItem; only a Coordinator or scoped
delegate can authorize it into an executable obligation.
_Avoid_: Assignment, Message-only authority

**Work Offer**:
An expiring invitation for an eligible Worker to accept a WorkItem after local admission control.
_Avoid_: Assignment, ownership

**Admission Control**:
The Worker's decision that an offered WorkItem fits its capability, authorization, queue capacity,
deadline, dependency, and budget constraints before acceptance.
_Avoid_: Coordinator assignment, scheduling priority

**Selection Basis**:
The auditable facts used to choose an offered Worker, including capability matches, authorization
eligibility, availability, cost, reliability Evidence, and applied policy.
_Avoid_: Private reasoning, ranking prompt

**Work Contract**:
The goal, deliverables, acceptance criteria, inputs, permissions, deadline, and retry budget of a WorkItem.
_Avoid_: Prompt, request

**Artifact**:
An immutable content-addressed deliverable produced or referenced by Mission work.
_Avoid_: Attachment, message payload

**Evidence**:
Recorded facts used to evaluate an Artifact or WorkItem against its acceptance criteria.
_Avoid_: Opinion, chain-of-thought

**Checkpoint**:
A structured, durable, safe-to-resume execution state reference used for blocking, recovery, and
cooperative preemption.
_Avoid_: Percentage progress, private memory dump

**Context Package**:
A signed, versioned summary with provenance that gives an Agent scoped Mission context.
_Avoid_: Memory dump, transcript

## Coordination and state

**Command**:
A signed request by an authorized actor to make one structured state transition.
_Avoid_: Message, Event

**Action ID**:
A stable identifier chosen by a Command actor so retries of identical signed content are
idempotent and conflicting reuse is rejected.
_Avoid_: Event ID, attempt number

**Correlation ID**:
An identifier linking related Commands, Events, and external work without imposing ordering.
_Avoid_: Group sequence, Action ID

**Event**:
An immutable accepted fact in a Group's monotonic history.
_Avoid_: Command, notification

**Cursor**:
The highest contiguous Group Event position durably processed by an Agent.
_Avoid_: Offset, timestamp

**Attention Filter**:
A delivery preference that narrows live Group traffic while preserving the member's right to
retrieve authorized history.
_Avoid_: Membership visibility, access control

**Delivery**:
At-least-once transport of durable Events to an authorized Group member, with deduplication by
Event ID and progress acknowledged by Cursor.
_Avoid_: Exactly-once side effect

**Replay**:
Ordered redelivery of a Group's Events after a durable Cursor, subject to Membership visibility.
_Avoid_: Cross-Group ordering

**Membership Epoch**:
A monotonic value fencing Commands, tokens, and Delegation Grants issued under an older version
of one Group Membership.
_Avoid_: Session Epoch, Presence

**Coordinator Epoch**:
A monotonic value fencing a replaced Coordinator, its prior role lease, and its Delegation Grants.
_Avoid_: Ownership Epoch, leader-election term

**Ownership Lease**:
A bounded reservation that keeps one Worker assigned to an exclusive WorkItem before and between
active execution periods.
_Avoid_: Execution Lease, permanent assignment

**Execution Lease**:
A renewable, fenced grant allowing one Worker Session and Ownership Epoch to execute an exclusive
WorkItem. Execution Commands reference its stable Lease ID; short-lived capability tokens bind to
that Lease ID and may rotate without changing the lease.
_Avoid_: Lock, assignment

**Session Epoch**:
A monotonic value fencing replaced runtimes that share one Agent identity over time.
_Avoid_: WorkItem lease

**Ownership Epoch**:
A monotonic value fencing previous owners of an exclusive WorkItem.
_Avoid_: Session epoch

**Scheduler**:
The Worker-owned policy that selects eligible WorkItems across its per-Group queues and capacity slots.
_Avoid_: Coordinator, queue

**Capacity Slot**:
One isolated unit of Worker concurrency with its own Group context, credentials, checkpoint, and
side-effect scope.
_Avoid_: Agent identity, thread

**Resource Budget**:
Hard limits on financial cost, model tokens, tool calls, compute time, wall time, and external
actions allocated to a Mission, WorkItem, or Delegation Grant.
_Avoid_: Estimate, priority

**Budget Ledger**:
The authoritative hierarchical account of allocated limits, cumulative usage, and remaining
capacity for Missions and WorkItems.
_Avoid_: Local token meter, cost estimate

**Resource Usage Record**:
A signed nonzero resource delta bound to a WorkItem, Ownership Epoch, and Execution Lease and
atomically rolled through its budget ancestry.
_Avoid_: Progress percentage, budget allocation

**Approval**:
A durable signed decision accepting a specific Mission revision and exact Artifact set.
_Avoid_: Coordinator review, verification

**Execution Approval**:
A time-bounded signed human decision permitting specified high-risk operations, resources, and
budget for one WorkItem Ownership Epoch before a capability token is issued.
_Avoid_: Final Approval, Work Offer

**Cooperation Override Grant**:
A durable, one-shot approval for one Principal to exceed one cooperation limit through one exact
Command in one Mission Group before a stated expiry.
_Avoid_: Boolean override, reusable exemption

**Group Snapshot**:
A signed archival projection through a specific Group sequence, linked to the retained Event and
policy-log history from which it was produced.
_Avoid_: Mutable database backup

**Policy Log**:
An append-only record of authorization, budget, risk, escalation, and redaction decisions needed
to audit a Group's state transitions.
_Avoid_: Agent reasoning trace

**Extension Profile**:
An organization-approved, versioned schema and semantics package that cannot override core invariants.
_Avoid_: Plugin, arbitrary event type

## Localized terminology

**Child Mission display name**:
Localized prose uses `子任务` in Simplified Chinese, `子任務` in Traditional Chinese,
`子ミッション` in Japanese, `Mission hija` in Spanish, `Mission enfant` in French, and
`untergeordnete Mission` in German. Each name still denotes a complete Child Mission with its own
Group, Coordinator, budget, and Approval lifecycle; Chinese prose uses `工作项` or `工作項` for a
WorkItem.
_Avoid_: `子 Mission`, `子使命`, using `子任务` or `子任務` for a WorkItem
