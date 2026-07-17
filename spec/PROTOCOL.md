# MissionWeaveProtocol 0.1

Status: Draft Standard, version `0.1.0`.

This document defines version 0.1 of MissionWeaveProtocol. The key words **MUST**, **MUST NOT**,
**REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**,
**NOT RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described
by BCP 14 when, and only when, they appear in all capitals as shown here.

## 1. Purpose and scope

MissionWeaveProtocol is a group-oriented cooperation protocol for autonomous Agents operating
inside one trusted Organization. It lets an Agent participate in many Mission Groups
concurrently, exchange durable Messages with peers, accept explicit WorkItems into per-Group
queues, schedule those WorkItems across Groups, publish verifiable Artifacts, and obtain human
approval of completed Missions.

MissionWeaveProtocol is not Agent-to-Agent RPC. Agents are peers in Conversation and MAY
initiate Messages or WorkItem proposals at any time. Structured authority is nevertheless
explicit: a Message never authorizes a side effect, and organization infrastructure validates
all Commands that change Mission state.

MissionWeaveProtocol 0.1 standardizes:

* Agent identity, Agent Cards, Presence Records, and runtime fencing;
* one temporary Group and one monotonic Event history per Mission;
* a replaceable Coordinator and a human MissionOwner;
* Membership, Conversations, Messages, WorkItems, Work Contracts, Artifacts, Evidence,
  Context Packages, leases, budgets, and approvals;
* durable Commands, immutable Events, replay, acknowledgements, and idempotency;
* per-Group Worker queues and privacy-preserving cross-Group scheduling signals;
* recursive child Missions for complex decomposition;
* canonical JSON over an authenticated WebSocket-over-TLS binding; and
* governed Extension Profiles.

MissionWeaveProtocol 0.1 deliberately does not define cross-organization federation, physical
peer-to-peer routing, Group end-to-end encryption, distributed consensus, model prompts,
private model reasoning, a knowledge-base API, an Artifact object-store API, or the
implementation of the Organization's policy and authorization services.

## 2. Normative references and data conventions

Implementations MUST follow these external specifications where referenced:

* RFC 2119 and RFC 8174 (BCP 14), normative language;
* RFC 3339, timestamps;
* RFC 6455, WebSocket;
* RFC 8446, TLS 1.3;
* RFC 8785, JSON Canonicalization Scheme (JCS);
* RFC 8032, Ed25519;
* JSON Schema Draft 2020-12; and
* RFC 9457 principles for structured protocol errors, where applicable.

All protocol objects MUST be valid JSON. Durable protocol objects MUST conform to the JSON
Schemas in `schemas/`. A timestamp MUST be an RFC 3339 `date-time` normalized to UTC when it
is hashed or signed. A content hash in v0.1 MUST use lower-case hexadecimal SHA-256 and the
form `sha256:<64 hex digits>`. Integers used for sequences, revisions, epochs, and budgets
MUST be non-negative safe JSON integers; Group Event sequences start at 1.

An identifier MUST be globally unique within the identifier's kind and MUST be serialized as
an absolute URI. UUID identifiers SHOULD use lower-case `urn:uuid:` form. Implementations
MUST compare identifiers byte-for-byte after the URI normalization rules chosen by the
issuing Organization; recipients MUST NOT invent additional normalization.

## 3. Terms and roles

The domain glossary in [`../CONTEXT.md`](../CONTEXT.md) is normative. The following role
rules refine that vocabulary:

* An **Organization** is the sole trust and governance boundary in v0.1.
* An **Agent** is one stable identity with at most one active runtime session. Horizontal
  scale-out is represented by separately registered Agent identities.
* A **MissionOwner** is the accountable Group member for directives, approval, and normal
  cancellation. It is a human for a root Mission. For a child Mission, the Parent Coordinator
  fills this role under the root human's accountability.
* A **Coordinator** is an Agent holding a renewable role lease. Exactly one Coordinator
  epoch MAY be active for a Mission at a time.
* A **Worker** is an Agent that accepts WorkItems into its own scheduling queues. The same
  Agent MAY be a Worker in many Groups.
* A **Group Authority** is Organization infrastructure that authenticates sessions, validates
  Membership and policy, serializes structured transitions, and appends Events. It is not a
  semantic manager and does not decide what Agents should say or how they should reason.

The Group Authority is one logical authority per Group. An implementation MAY replicate it
internally, but consensus, leader election, and replica topology MUST NOT be exposed as
MissionWeaveProtocol semantics. This choice provides deterministic exclusive ownership
without requiring Agents to resolve split-brain execution socially.

## 4. Core invariants

A conforming implementation MUST preserve all of the following invariants:

1. **One Mission, one Group.** Each Mission owns exactly one primary Group and each primary
   Group belongs to exactly one Mission.
2. **Conversation is not authority.** A Message, mention, summary, Context Package, or model
   output MUST NOT by itself authorize a tool call, business action, WorkItem assignment,
   budget expenditure, or permission grant.
3. **Structured execution authority.** A consequential action MUST be connected to an
   accepted WorkItem, the current ownership epoch, a valid Execution Lease, applicable
   policy approval, and a scoped capability token.
4. **One active runtime.** A state-changing Agent Command MUST carry the current Session
   Epoch. A lower epoch MUST be rejected even if its WebSocket remains connected.
5. **Exclusive work is fenced.** At most one current ownership epoch exists for an exclusive
   WorkItem. Results from a stale epoch MAY be retained as non-authoritative Evidence but
   MUST NOT complete the WorkItem.
6. **Append-only history.** Accepted Events and committed Messages are immutable. Correction,
   retraction, redaction, revocation, and remediation are new Events.
7. **Per-Group order only.** Every Group has one monotonic Event sequence.
   MissionWeaveProtocol defines no global order or atomic transaction across Groups.
8. **At-least-once delivery.** Events MAY be delivered more than once. Stable identifiers and
   idempotent processing MUST make each accepted state transition observable once.
9. **Mission isolation.** Mission content, credentials, intermediate state, and Agent memory
   are Group-scoped by default. Cross-Group disclosure MUST be explicit and authorized.
10. **Human final approval.** A root Mission becomes completed only after its MissionOwner
    approves an exact Mission revision and Artifact set. Coordinator review is not final
    human Approval.
11. **Budgets and permissions narrow downward.** WorkItem and child-Mission budgets,
    capabilities, and resource permissions MUST NOT exceed their parent grants.
12. **No private Mission side-channel.** Mission-related Agent communication MUST be recorded
    in the Mission Group or a linked, access-controlled Conversation visible to the
    Coordinator and MissionOwner.
13. **No private reasoning requirement.** Agents MUST publish decisions, inputs, evidence,
    blockers, and outcomes needed for audit; they MUST NOT be required to publish private
    chain-of-thought, hidden prompts, or raw internal memory.

## 5. System architecture

A MissionWeaveProtocol deployment contains at least:

* an Organization-controlled Agent Registry;
* a Group Authority and durable Group Event store;
* an Authorization Service that evaluates policy and issues capability tokens;
* one or more independently scheduled Agents;
* Artifact storage addressed by content hash; and
* a human interface for Mission directives, monitoring, intervention, and Approval.

The authoritative state consists of Missions, Memberships, WorkItems, ownership and lease
epochs, deduplication receipts, approvals, and Group Events. Agent-local Cursors, per-Group
queues, checkpoints, outboxes, inboxes, and Scheduler state are rebuildable projections.
Loss of an Agent's local database MUST NOT change authoritative Mission state.

PostgreSQL and Agent-local SQLite are RECOMMENDED for the v0.1 reference implementation,
and content-addressed object storage is RECOMMENDED for Artifacts. These products are not
wire-protocol requirements.

## 6. Identity, Agent Registry, and sessions

### 6.1 Agent Cards

The Organization MUST issue, verify, version, and sign each Agent Card. An Agent MUST NOT be
trusted merely because it self-declares a capability. The Agent Card MUST separate:

* stable identity, ownership, endpoint, public keys, and supported protocol versions;
* versioned Organization-governed capabilities with declared input/output schemas,
  constraints, and verification Evidence; and
* maximum supported concurrency.

Capability is not authorization. An Agent Card MUST NOT contain reusable credentials or
grant access to tools or business data. Authorization eligibility and current policy remain
Organization decisions.

Assignments MUST pin the Agent Card version and every required capability version. A
compatible in-place upgrade MAY continue under Organization policy. An incompatible upgrade
MUST checkpoint active work and obtain renewed acceptance before execution continues. Every
Artifact MUST record the producing Agent Card and capability versions.

The Registry SHOULD maintain capability-specific, contextual performance records separately
from Agent Cards. Records MAY include completion, failure, reassignment, human change-request,
deadline, budget, and lease-expiry outcomes. An implementation SHOULD NOT reduce performance
to one opaque global reputation score.

### 6.2 Presence Records

Presence is ephemeral and MUST be separate from the stable Agent Card. A Presence Record MAY
report online state, currently available execution slots, capability availability, estimated
response latency, and last heartbeat. A stale Presence Record MUST NOT be treated as an
assignment acceptance or lease renewal.

Presence updates MAY be carried in authenticated `PING` frames and do not require an
individual durable signature. Presence MUST NOT expose another Group's identity, content,
WorkItems, or exact queue position.

### 6.3 Authentication and Session Epoch fencing

Each Agent MUST have at least one Organization-registered Ed25519 public key. The v0.1
WebSocket handshake uses a fresh server challenge:

1. the Agent sends `HELLO/client_init` with its Agent ID, key ID, nonce, and supported
   protocol versions;
2. the server replies `HELLO/server_challenge` with an unpredictable challenge and selected
   version;
3. the Agent replies `HELLO/client_response` with an Ed25519 signature over the canonical
   challenge transcript; and
4. the server replies `HELLO/server_accept` with a short-lived session token and a newly
   issued Session Epoch.

Issuing epoch `n + 1` invalidates every session at epoch `n` or lower for that Agent ID.
The Group Authority MUST validate the Session Epoch on every state-changing Agent Command.
Human and Organization-service Commands do not carry an Agent Session Epoch and MUST NOT invent
one. A restarted runtime MAY reclaim its stable Agent ID; two runtimes MUST NOT operate that
identity concurrently.

Durable Commands and Artifact manifests MUST be individually signed. Heartbeats and Presence
Records rely on the authenticated session. Long-lived shared API keys are NOT RECOMMENDED.
An implementation MAY add mTLS or workload-identity authentication, provided it preserves
the Agent ID and fencing semantics.

### 6.4 Signature input

Unless an Extension Profile specifies an additional signature, a signature covers the JCS
canonical form of the complete object with its top-level `signature` member omitted. The
Command signature therefore covers at least its Action ID, actor, applicable Session,
Membership, and Coordinator Epochs, Group ID when present, kind, payload, correlation ID,
timestamp, and extensions. An Event signature is made by the accepting authority and covers its
Event ID, Group sequence when present, cause, actor, payload, and time.

Signature verification MUST use the pinned key ID and key validity interval. Implementations
MUST reject altered signed content, an unknown or revoked key, or an invalid algorithm.

## 7. Mission and Group lifecycle

### 7.1 Creation

A Mission MUST declare a bounded objective, machine-readable definition of done, deadline,
enforceable budget, risk/approval policy, and MissionOwner. A root Mission's MissionOwner
MUST be human. Creation allocates exactly one Group and one Group-level Conversation. Mission
IDs and Group IDs MUST remain stable.

The Mission lifecycle is:

| Current state | Command or cause | Next state | Authority |
| --- | --- | --- | --- |
| none | `mission.create` with a Coordinator lease | `active` | human MissionOwner, possibly through the control plane |
| none | `mission.create_follow_up` linked to an approved Mission | `active` | the same human MissionOwner |
| none | `mission.create_child` linked to a parent WorkItem | `active` | Parent Coordinator as child MissionOwner |
| `active` | `mission.submit_for_approval` | `awaiting_approval` | current Coordinator |
| `awaiting_approval` | `mission.request_changes` | `active` | MissionOwner |
| `awaiting_approval` | `mission.approve` | `approved` | MissionOwner |
| non-terminal | `mission.cancel` or parent-cancellation propagation | `cancelled` | MissionOwner or Organization policy |
| non-terminal | `mission.terminate` or declared child-failure propagation | `failed` | Coordinator or Organization policy |

`approved`, `cancelled`, and `failed` are terminal. An approved Mission MUST NOT be
reopened or rewritten. Corrections, approval revocation, or remediation MUST create a linked
follow-up Mission; revocation remains a new Event and does not erase the original Approval.

The Coordinator MAY checkpoint or block individual WorkItems and recommend cancellation but MUST
NOT normally cancel the Mission. The MissionOwner MAY issue directives to the Coordinator. Direct human
assignment to a Worker is an explicit, audited emergency override and MUST still pass Worker
acceptance, capability, authorization, budget, and lease rules.

### 7.2 Coordinator lease

Exactly one Coordinator lease epoch MAY be current. The lease identifies the Agent,
Coordinator Epoch, Session Epoch, expiry, and renewal policy. Only the current Coordinator
epoch may authorize or assign WorkItems, accept Worker results, submit the Mission, or create
child Missions.

If the Coordinator stops renewing its lease, the Organization control plane or MissionOwner
MAY appoint a replacement with a higher Coordinator Epoch. Events produced by the former
Coordinator remain valid history, but its later coordination Commands MUST be rejected as
stale. The replacement MUST receive a signed Context Package and MUST reconcile current
WorkItem state before issuing new assignments.

The Coordinator SHOULD reserve capacity for planning, monitoring, integration, and
escalation. It MAY execute coordination-native WorkItems and exceptional fallback work, but
MUST NOT be the sole reviewer of its own output.

### 7.3 Progress and completion

Authoritative Mission progress MUST be derived from the WorkItem dependency graph, accepted
Evidence, critical path, blockers, deadlines, and approval state. A Coordinator MAY publish
narrative summaries, risks, and forecasts but MUST NOT replace derived state with an
unsubstantiated percentage.

Before submission, the Coordinator MUST review all required WorkItem results and acceptance
Evidence. It then emits `mission.submit_for_approval` for a specific Mission revision and
Artifact set. The MissionOwner either emits a signed Approval or a signed change request.
Requested changes reopen the same Mission, and the Coordinator creates revised or corrective
WorkItems without deleting earlier submissions.

### 7.4 Retention and archival

An active Group MUST retain its complete Event history. Archival MUST produce a signed final
snapshot containing decisions, WorkItems, approvals, and Artifact references. The original
encrypted audit log is retained according to Organization policy. Legal deletion or security
redaction MUST append an auditable tombstone; it MUST NOT silently rewrite prior Event IDs or
sequence numbers. Reconnection MAY use a snapshot followed by later Events.

## 8. Membership, visibility, and attention

Membership binds an Agent or human to one Group, an epoch, a role, a visibility starting
sequence, and explicit capabilities. A Group-scoped Agent or human Command MUST carry its current
Membership Epoch; a Command from a revoked or stale Membership Epoch MUST be rejected.
Organization-service Commands are authenticated and authorized by Organization policy rather than
by inventing a Group Membership Epoch. MissionOwner and Coordinator Memberships MUST have complete
Group visibility.

Worker Membership SHOULD be just in time:

1. the Coordinator selects a candidate and grants scoped provisional Membership;
2. the Worker receives an expiring offer and signed Context Package;
3. accepting the offer activates Membership and creates ownership; and
4. Membership ends when the Worker has no WorkItems or review obligations, or the Mission is
   archived.

A late-joining Worker MUST NOT automatically receive unrestricted history. It receives the
Context Package, relevant Conversation and Artifact references, and only history allowed by
its Membership. It MAY retrieve cited source Events when authorized.

All committed Messages remain in the durable Group history, but live delivery MUST support
attention filters. A Worker SHOULD receive its WorkItem Conversations, direct mentions,
important announcements, and subscribed cross-cutting topics. Other authorized history is
retrievable on demand. The Coordinator MAY consume all Messages or continuous summaries. The
MissionOwner SHOULD receive summary notifications while retaining full inspection rights.

An Agent's noisy Group MUST NOT starve traffic from another Group. Gateways MUST implement
per-Group flow control and SHOULD allow independent subscription cursors.

## 9. Conversations and Messages

Creation of a Mission creates a Group-level planning Conversation. Every WorkItem MUST own a
dedicated Conversation. An implementation MAY create a review Conversation and linked,
restricted Conversations for sensitive material. Restricted Conversations remain within the
Mission's audit boundary and MUST be inspectable by the Coordinator and MissionOwner.

A committed Message contains completed content only. MissionWeaveProtocol 0.1 does not define
partial token or `message.delta` streaming. Message content MAY include text and references to
Artifacts or structured data. Large binary data MUST NOT be embedded; it is transferred as an
Artifact reference.

Every Message object has `authority: false`. A Message such as "deploy immediately" is only
conversation. To act, an authorized actor must create or authorize a WorkItem through a
Command. Interfaces MUST NOT present a Message as an executable assignment.

Any Group Agent MAY:

* post a Message;
* propose a WorkItem;
* request help; and
* discuss context directly with peers in the relevant Conversation.

### 9.1 Delegated work authority

Only the current Coordinator, a MissionOwner emergency override, or an Agent holding an
explicit scoped Delegation Grant MAY authorize and offer a WorkItem. The `work_delegate` role
only makes a Group member eligible to use a Grant; the role alone conveys no work-authoring
authority. A delegated `work.authorize` or `work.offer` Command MUST cite a persisted Grant ID.

Only the current Coordinator MAY issue `membership.grant_delegation`. The resulting Grant MUST
record its Grant ID, grantee Agent ID, Mission ID, Group ID, target WorkItem ID, allowed
capability IDs and minimum versions, currency and explicit ceilings for all six Resource Budget
dimensions, maximum descendant depth, grantee Membership Epoch, Coordinator Epoch, issuing
Coordinator, grant time, and expiry. Acceptance emits `membership.delegation.granted`.

The target WorkItem is the Grant's scope root. The grantee MAY offer that root or an existing
descendant, and MAY authorize a new descendant only when `parentWorkItemId` explicitly links it
into that subtree. Each required Work Contract capability MUST be allowed by the Grant and meet
its minimum version. The cumulative budgets of all WorkItems created or offered under the Grant
MUST remain within every Grant ceiling. Descendant depth MUST satisfy both the Grant maximum and
Organization cooperation policy.

At every use, the actor MUST be the grantee and hold an active `work_delegate` Membership whose
epoch equals the Grant's grantee Membership Epoch. The Grant's Mission, Group, Coordinator Epoch,
issuer, and validity interval MUST still match current authoritative state. A replaced
Coordinator, changed or ended Membership, expired Grant, missing target, or target that becomes
failed, cancelled, or verified immediately invalidates further use. A Grant is non-transferable.
Workers without a valid Grant may propose sub-work, but MUST NOT create executable obligations
for another Worker.

Accepted Messages are immutable. A correction, retraction, or redaction MUST append a new
Event referencing the original Message ID. Redaction requires an auditable policy reason.
User interfaces MAY display the latest effective form while retaining the Event chain.

## 10. WorkItems and Work Contracts

### 10.1 Required Work Contract

Every WorkItem MUST carry a versioned, machine-readable Work Contract containing:

* a goal and required deliverables;
* acceptance criteria and required Evidence;
* input and dependency references;
* allowed tools, data, operations, and resource constraints;
* required capability IDs and versions;
* deadline, requested urgency, and business impact;
* financial, token, tool-call, compute, wall-clock, and side-effect budgets as applicable;
* retry attempts, backoff, deadline, and cost policy; and
* risk classification and any pre-execution approval requirement.

An essential ambiguity MUST be raised in the WorkItem Conversation before acceptance; the Worker
MUST NOT accept the WorkItem into its execution queue. The Coordinator resolves it by issuing a
new `work.offer` with the corrected contract or by authorizing a replacement WorkItem. A materially
revised Work Contract increments its revision and requires renewed Worker acceptance.
Natural-language prose MAY supplement, but MUST NOT replace, the contract fields.

### 10.2 WorkItem state machine

The core WorkItem states and transitions are:

| Current state | Transition | Next state | Notes |
| --- | --- | --- | --- |
| none | `work.propose` | open Work Proposal | Any Group member may propose; no WorkItem exists yet |
| none or open Work Proposal | `work.authorize` | `open` | Coordinator or scoped delegate creates the WorkItem |
| `open`, `offered`, `queued`, `active`, `blocked`, or `failed`, with no live owner | `work.offer` | `offered` | Creates, replaces, or extends a durable offer; an expired owner is fenced first |
| `offered` | `work.accept_offer` | `queued` | Atomic ownership epoch begins |
| `offered` | offer expiry | `offered` | Expiry invalidates acceptance but does not itself append an Event or change state |
| `queued` | `approval.grant_execution` when required | `queued` | Satisfies the start gate without executing work |
| `queued` | `work.start` | `active` | Valid ownership and Execution Lease required |
| `active` | `work.checkpoint` | `queued` | Durable progress releases execution while retaining a bounded ownership lease |
| `active` | `work.block` | `blocked` | Checkpoint and bounded blocked lease |
| `blocked` | `work.unblock` | `queued` or `open` | Re-enters its queue or is re-offered after ownership expiry |
| `active` | `work.submit` | `submitted` | Artifacts and Evidence required |
| `submitted` | `work.accept_result` | `verified` | Coordinator review succeeds |
| `open`, `offered`, `queued`, `active`, `blocked`, or `submitted` | `work.fail` | `failed` | Failure Evidence required; a Coordinator may later issue a new `work.offer` |
| `open`, `offered`, `queued`, `active`, `blocked`, or `submitted` | `work.cancel` | `cancelled` | Cleanup policy applies |
| `open`, `offered`, `queued`, `active`, or `blocked` | `mission.create_child` | `blocked` | Ownership is fenced while the linked child Mission runs |
| `blocked` | linked child Mission approval | `verified` | Child Approval becomes parent WorkItem Evidence |
| `blocked` | linked child Mission failure | `blocked` or `failed` | The declared child-failure policy controls propagation |
| `open`, `offered`, `queued`, `active`, `blocked`, or `submitted` | parent Mission failure or cancellation | `failed` or `cancelled` | Terminal Mission state propagates to unfinished WorkItems |

`verified` and `cancelled` are terminal for that WorkItem revision. `failed` returns control
to the Coordinator and may transition only through a new `work.offer`; the Coordinator MAY
instead create a replacement WorkItem or cancel the branch at Mission level. Implementations
MUST reject transitions not permitted by this table and the current aggregate revision.

### 10.3 Offers, admission control, and ownership

An offline Worker MAY receive a durable offer with an expiration time. The offer MUST NOT
reserve exclusive ownership before acceptance. Exclusive WorkItems SHOULD be offered
sequentially to the highest-ranked eligible Worker. For urgent placement the Coordinator MAY
offer to a bounded candidate set; the first valid acceptance atomically wins a new Ownership
Epoch and every losing offer is withdrawn before a loser may execute.

Acceptance means a durable scheduling commitment, not immediate execution. A Worker MUST
perform admission control against queue capacity, concurrency, capability availability,
deadlines, authorization eligibility, dependencies, and budgets. It MUST decline when it
cannot make a credible commitment and SHOULD use a structured reason such as `capacity`,
`deadline`, `capability`, `authorization`, `dependency`, or `budget`.

Every assignment MUST record a structured selection basis: required capability matches,
authorization eligibility, availability estimate, expected cost, capability-specific
reliability Evidence, and applied policy rules. Private chain-of-thought MUST NOT be included.

### 10.4 Dependencies and dynamic planning

A Mission's WorkItems form an evolving directed acyclic graph. A Coordinator MAY begin
execution before the complete graph is known, add WorkItems as discoveries occur, and run
independent branches in parallel. A WorkItem is eligible only when its declared dependencies
satisfy the contract's dependency policy. Dependency cycles MUST be rejected.

There is no cross-Group transaction. Cross-Group relationships use stable correlation IDs,
parent/child Mission links, Artifacts, and compensating WorkItems.

## 11. Scheduling, execution, and recovery

### 11.1 Per-Group queues and global Scheduler

Each Worker MUST maintain a distinct Event inbox, Cursor, and Work queue for each Group. The
queues are durable local projections of accepted Group Events and MUST be rebuildable by
replay. Mission, ownership, lease, and WorkItem status remain authoritative in the Group log.

A Worker-owned Scheduler selects eligible WorkItems from all per-Group queues into declared
isolated execution slots. The Scheduler has final authority over cross-Group order. A
Coordinator supplies requested urgency, deadline, and business impact but MUST NOT force its
Mission ahead of others. Escalation of organization priority goes through policy or the
MissionOwner.

The Scheduler MUST implement weighted fairness and anti-starvation. Effective order SHOULD
consider organization priority class, deadlines, aging, per-Group quotas, risk gates, and
resource availability. Pure unbounded highest-priority-first scheduling is non-conforming.

An Agent Card declares maximum concurrency; Presence reports current capacity. Each active
slot MUST isolate Mission context, credentials, checkpoints, tool budgets, and side-effect
keys from other slots.

### 11.2 Scheduling disclosure

On acceptance and material schedule changes, a Worker SHOULD publish an estimated start
window, estimated completion, confidence, capacity status, and calculation time. It MUST NOT
expose names, content, assignments, or exact global queue positions from another Group.

### 11.3 Execution Leases and preemption

Queued ownership and active execution use renewable, fenced leases. An ownership grant MUST
include an Ownership Epoch and start-by deadline. Starting work requires an Execution Lease
with a stable Lease ID bound to Agent ID, Session Epoch, WorkItem ID, Ownership Epoch, start,
renewal history, and expiry. Every renewal, checkpoint, block, Artifact publication, submission,
and Worker-reported failure MUST reference the current Lease ID. A delayed Command carrying an
older Lease ID MUST be rejected even when its Ownership Epoch is unchanged.

Capability tokens bind to the Execution Lease ID, not the reverse. This permits tokens to be
rotated or narrowed while one lease remains active; every token still expires no later than the
lease boundary under which it was issued. Checkpoint, block, and submission release the lease;
timeout expires it; Session replacement, reassignment, cancellation, and failure revoke it.
Opening a replacement Agent Session MUST revoke that Agent's active leases and return affected
WorkItems to `queued` before the new runtime may start them under new leases.

Priority changes immediately reorder queued WorkItems. Active work MUST NOT be forcibly
interrupted at an unsafe point. Preemption is cooperative:

1. the Scheduler requests preemption;
2. the Worker reaches a safe, idempotent checkpoint;
3. it emits the checkpoint and pauses;
4. its execution slot is released; and
5. the paused WorkItem re-enters its Group queue for later resumption.

### 11.4 Progress, blocking, and retries

Progress reports MUST be structured around current phase, completed milestones, next
checkpoint, blockers, revised estimate, and Evidence references. Arbitrary percentages are
non-authoritative. Workers SHOULD report at meaningful checkpoints, when an estimate changes
materially, or when blocked.

When blocked, a Worker MUST checkpoint, emit `work.blocked` with required resolution, and
release its execution slot. Ownership MAY remain during a bounded blocked lease. The
Coordinator may resolve the blocker, authorize proposed sub-work, or reassign. Unblocked work
returns to its per-Group ready queue.

Automatic retries are limited by the Work Contract's attempt, backoff, cost, and deadline
budgets. External attempts MUST use the WorkItem execution idempotency key or a deterministic
derived attempt key. Exhaustion or permanent failure emits `work.failed` with Evidence.

### 11.5 Worker and Coordinator failure

If a Worker misses its start deadline or stops renewing a lease, the Coordinator MAY reassign
from the latest checkpoint with a higher Ownership Epoch. A late result from the old owner
MAY be stored for audit but MUST NOT complete the WorkItem.

If the Group service is unavailable, a Worker MAY continue already-active reversible
computation for a bounded lease-grace period and buffer signed progress and checkpoints. It
MUST NOT start new WorkItems or perform new high-risk, irreversible, or externally visible
actions without a currently valid lease and capability token. It MUST reconcile on reconnect
before submission or further side effects.

Each buffered Command MUST carry the critical
`urn:missionweaveprotocol:extension:bounded-offline-execution` binding. The binding records the
Agent, Group, WorkItem, original Session Epoch, Ownership Epoch, historical Execution Lease ID,
disconnect time, buffer time, grace deadline, historical lease expiry, and the six-dimensional
resource usage delta. On reconnect the Worker MUST preserve that binding but rebase and re-sign
the Command with an `issuedAt`, Session Epoch, and Membership Epoch from the current
authenticated session. The Group Authority MUST reject progress buffered outside the historical
lease/grace window, after lease closure, for a changed owner, or outside the bound WorkItem
Conversation.

Reconciliation and its resource charge are one authoritative transaction. For every nonzero
offline delta, the Group Authority MUST append an
`ext.missionweaveprotocol.core.resource_usage_recorded` Event that identifies both the
historical execution session and the reconciliation session, updates the WorkItem and complete
budget ancestry, and then applies the Message or checkpoint. Budget overflow MUST reject both
the charge and the progress Command without a partial Event or state change.

## 12. Authorization, budgets, and side effects

After WorkItem acceptance and all required approvals, the Authorization Service issues a
short-lived least-privilege capability token. The token MUST be bound to:

* the Worker Agent ID and current Session Epoch;
* WorkItem ID and Ownership Epoch;
* the current Execution Lease ID;
* allowed tools, resources, data, and operations;
* financial, token, call, compute, time, and side-effect limits; and
* an expiration no later than the applicable Execution Lease.

The Coordinator MAY request authorization but MUST NOT manufacture, copy, or forward a
Worker's credential. Tokens and secrets MUST NOT appear in Messages, Agent Cards, Context
Packages, Artifacts, or Group Events. Expired, revoked, mismatched, or over-budget tokens MUST
be rejected.

Organization policy MUST be able to place a WorkItem into
`awaiting_execution_approval` before production deployment, payments, external
communications, destructive changes, or sensitive-data access. The Authorization Service
MUST withhold the capability token until the signed approval gate is satisfied. Low-risk work
MAY proceed automatically under policy.

Mission and WorkItem budgets are mandatory protocol concepts. The MissionOwner sets Mission
limits, the Coordinator allocates no more than those limits to WorkItems and child Missions,
and the Authorization Service enforces hard limits. Budget exhaustion pauses affected work
and requires explicit escalation; Agents MUST NOT silently exceed a limit.

The Group Authority MUST persist an aggregate six-dimensional budget ledger. A signed
`ext.missionweaveprotocol.core.resource_usage_record` Command records a nonzero delta against
one WorkItem, Ownership Epoch, and Execution Lease ID; the corresponding
`ext.missionweaveprotocol.core.resource_usage_recorded` Event carries the delta, cumulative
usage, and remaining budget. Consumption MUST update the WorkItem and its complete
WorkItem/Mission ancestry in one atomic transition. A one-dimension overflow MUST reject the
whole transition as `BUDGET_EXCEEDED`. Capability-token budgets MUST be capped by both the Work
Contract and the authoritative remaining budget.

Cancellation or emergency termination MUST revoke relevant leases and capability tokens,
stop new assignments, and initiate contract-defined cleanup or compensation WorkItems where
needed.

## 13. Artifacts, Evidence, and Context Packages

### 13.1 Artifacts

An Artifact is immutable and content addressed. Binary content MUST be stored outside the
Group Event log. Its signed manifest MUST contain the content hash, media type and schema,
producer Agent and Agent Card version, Mission/Group/WorkItem IDs, source Artifact hashes,
relevant tool/model/capability versions, creation time, data classification, size, and
retrieval URI.

Derived Artifacts form a provenance graph. Implementations MUST verify the content hash when
retrieving an Artifact and MUST NOT treat a mutable URI as content identity.

### 13.2 Evidence-based review

A Worker's claim of completion is insufficient. WorkItem submission MUST include Evidence
mapped to acceptance criteria. Coordinator review SHOULD, in order:

1. validate Artifact integrity and required output schemas;
2. run deterministic tests or business rules where available;
3. request reviewer-Agent Evidence for semantic or qualitative criteria;
4. evaluate the combined Evidence; and
5. retain all results for final human Approval.

Evidence MUST record subject, criteria, method, result, producer, timestamp, and referenced
Artifacts. Evidence and decision records MUST NOT include private chain-of-thought.

### 13.3 Context Packages

A Context Package is a signed, versioned, scoped summary, never an authoritative replacement
for history. It MUST identify Mission and WorkItem scope, source Event range, Artifact hashes,
decisions, constraints, unresolved questions, generator, time, and signature. A Worker may
retrieve cited Events when its Membership permits. Updating a package creates a new version
and retains provenance to the previous version.

Group content MUST NOT enter another Mission's context by default. Reusable knowledge must be
explicitly published as an Organization-approved, classified, provenance-bearing Artifact.
Cross-Group forwarding requires permission checks and an auditable Event. The global
Scheduler may inspect scheduling metadata but MUST NOT inspect confidential Mission content.

## 14. Parent and child Missions

A sufficiently complex WorkItem MAY be promoted to a child Mission with its own Group,
Coordinator, WorkItem graph, Memberships, budget, deadline, and approval policy. The parent
WorkItem and child Mission MUST link to each other.

The parent-child graph MUST be acyclic. Child budgets, deadlines, capabilities, data access,
and permissions MUST be subsets of the parent. Organizations MUST configure a default maximum
depth and require explicit MissionOwner or policy approval beyond that threshold. Legitimate
approved complexity MUST be allowed; limits are guardrails, not hard protocol ceilings.

By default, the child Coordinator reviews and submits the child result and the Parent
Coordinator acts as child MissionOwner. Root-human approval is additionally required when
risk policy says so. The approved child result becomes Evidence and Artifacts for the parent
WorkItem.

A failed child Mission does not automatically fail its parent. It emits structured failure
Evidence and blocks or fails the parent WorkItem. The Parent Coordinator may replan, revise
scope, create a replacement child, or cancel. Failure propagates automatically only when the
parent completion policy declares that child indispensable with no alternative.

The Parent Coordinator receives child status changes, progress summaries, revised estimates,
blockers, budget/policy escalations, and final results. It MUST NOT be required to ingest every
child Message, but retains authorized on-demand inspection. The root MissionOwner MUST be able
to inspect the complete Mission tree.

## 15. Commands, Events, and concurrency

### 15.1 Commands

A Command is a signed request for one structured state transition. Every Command envelope MUST
contain a stable Action ID, protocol version, actor, kind, payload, correlation ID, issue time,
and signature. A Group-scoped Command MUST contain its Group ID. A state-changing Agent Command
MUST additionally contain the current Session Epoch and Membership Epoch. A human Command in an
existing Group MUST contain the current Membership Epoch and MUST NOT contain an Agent Session
Epoch. An Organization-service Command MUST NOT invent Agent Session or Membership Epochs.

`mission.create` and `mission.create_follow_up` carry the ID of the Group being created but omit
Membership and Session Epochs because the new Group Membership does not yet exist and human
Commands do not use Agent sessions. A control plane may authenticate, relay, and validate
`mission.create`, but the signed Command actor and resulting root MissionOwner remain that human;
the control plane does not become the MissionOwner. The Organization-owned
`ext.missionweaveprotocol.registry.agent_card_register` and
`ext.missionweaveprotocol.identity.session_open` bootstrap Commands omit Group ID and all three
role/session epochs.

An Agent Command whose authority derives from the current Coordinator lease MUST contain the
current Coordinator Epoch. This is required for `mission.renew_coordinator`,
`mission.submit_for_approval`, `mission.create_child`, `membership.grant_delegation`, and
`work.accept_result`, and for an Agent-issued `mission.terminate`. A service-issued
`mission.terminate` is instead authorized by Organization policy and does not carry a Coordinator
Epoch. A Command SHOULD contain the expected aggregate revision when modifying existing structured
state. A Command using a one-shot cooperation escalation MUST also contain
`cooperationOverrideGrantId`.

The same `(actor ID, Action ID)` with byte-equivalent canonical signed content MUST return the
original receipt and MUST NOT append a second state transition. Reuse of the same Action ID
with different canonical content MUST fail with `ACTION_ID_COLLISION`.

The Group Authority MUST authenticate the actor; validate Session and Membership Epochs,
schema, current aggregate revision, role, delegation, budget, policy, and lease; and either
reject the Command or append the resulting Event(s) atomically within that Group.

Core Command kinds are:

```text
mission.create                 mission.assign_coordinator
mission.renew_coordinator      mission.submit_for_approval
mission.approve                mission.request_changes
mission.cancel                 mission.terminate
mission.create_child           mission.create_follow_up
membership.change             membership.end
membership.grant_delegation
message.post                   message.correct
message.retract                message.redact
work.propose                   work.authorize
work.offer                     work.accept_offer
work.start                     work.checkpoint
work.block                     work.unblock
work.submit                    work.accept_result
work.fail                      work.cancel
artifact.publish               approval.grant_execution
policy.grant_cooperation_override
```

The reference core additionally defines Organization-owned `ext.missionweaveprotocol.*`
Commands for Agent Card registration, Session activation, dependency insertion, Execution
Lease renewal, authoritative resource-usage recording, and Group archival. A future Extension
Profile may standardize convenience Commands such as explicit offer decline, clarification,
or Mission pause, but those names are not v0.1 core transitions.

### 15.2 Events and Group order

An Event is an immutable accepted fact. A Group Event envelope MUST contain Event ID, Group ID,
strictly increasing Group sequence, aggregate revision, kind, actor, cause, correlation ID,
occurrence time, payload, and Group Authority signature. The Organization-scoped
`ext.missionweaveprotocol.registry.agent_card_registered` and
`ext.missionweaveprotocol.identity.session_opened` facts contain the common Event identity,
actor, cause, correlation, payload, time, accepting authority, and signature fields, but MUST NOT
contain Group ID, Group sequence, or Group aggregate revision.

The Group Authority assigns one monotonic sequence to every durable Group Event. This
sequence supplies deterministic display, recovery, and audit order. Ordinary Messages may be
logically concurrent even though the service assigns display order. Structured transitions
rely on the Event order and aggregate revisions.

Core Event kinds are the past-tense facts corresponding to core Commands, including:

```text
mission.created                 mission.coordinator.assigned
mission.coordinator.renewed     mission.submitted_for_approval
mission.approved                mission.changes_requested
mission.cancelled               mission.terminated
mission.child.created           mission.follow_up.created
membership.changed              membership.ended
membership.delegation.granted
message.posted                  message.corrected
message.retracted               message.redacted
work.proposed                   work.authorized
work.offer.created              work.offer.accepted
work.contract.revised           work.started
work.progressed                 work.checkpointed
work.blocked                    work.unblocked
work.submitted                  work.result.accepted
work.failed                     work.cancelled
artifact.published              approval.execution.granted
policy.cooperation_override.granted
group.snapshot.created          group.archived
```

`work.contract.revised` and `work.progressed` are core WorkItem facts emitted by the reference
Organization-owned dependency-insertion and Execution-Lease-renewal Commands. Agent Card and
Session activation facts retain their `ext.missionweaveprotocol.*` Event kinds.
`group.snapshot.created` and `group.archived` are core archival facts emitted atomically by the
Organization-owned `ext.missionweaveprotocol.core.group_archive` Command after its signed
snapshot and policy-log linkage validate.

Automatic Events MAY be caused by an accepted Command, prior Event, timer, or policy decision.
Events from different Groups have no defined order.

### 15.3 Optimistic concurrency

Structured aggregate Commands SHOULD provide `expectedRevision`. If it does not equal the
current revision, the Group Authority MUST reject the Command with `REVISION_CONFLICT` and
MUST NOT partially apply it. Atomic first-accept ownership, lease renewal, Membership change,
and Approval always require compare-and-set processing even if the wire field is omitted by a
privileged internal actor.

## 16. Delivery, replay, and acknowledgement

MissionWeaveProtocol promises at-least-once Event delivery. A recipient MUST deduplicate by
Event ID and MUST process each Group in sequence order. It MAY buffer an out-of-order Event,
but MUST NOT advance its durable Cursor over a gap.

A Cursor is the highest contiguous Group sequence durably processed by an Agent. An `ACK`
frame reports one or more Cursors. Acknowledgement permits delivery cleanup but MUST NOT delete
the authoritative Group history. Reconnection uses `SUBSCRIBE.afterSequence`; the server
replays Events after that position, possibly including duplicates around a prior disconnect.

If an old Cursor is no longer available in the online log, the server returns
`CURSOR_TOO_OLD` and a signed snapshot reference. The Agent restores the snapshot, verifies
its hash/signature, and resumes from the snapshot sequence.

External tool operations MUST use a stable idempotency key derived from Mission ID, WorkItem
ID, Ownership Epoch, and logical operation ID. Network delivery alone can never guarantee
exactly-once external side effects.

## 17. WebSocket binding

### 17.1 Connection

MissionWeaveProtocol 0.1 servers MUST provide WebSocket over TLS 1.3 (`wss`). A single authenticated
connection multiplexes all Groups used by one Agent. Each WebSocket message MUST contain
exactly one UTF-8 JSON text frame conforming to `schemas/websocket-frame.schema.json`.
Binary WebSocket messages MUST NOT carry MissionWeaveProtocol objects or Artifact content in v0.1.

The core frame types are `HELLO`, `SUBSCRIBE`, `COMMAND`, `EVENT`, `ACK`, `PING`, and `ERROR`.
Partial Message streaming frames are not defined.

### 17.2 Subscriptions

After authentication, a client sends `SUBSCRIBE` with Group IDs, per-Group replay positions,
and optional attention filters. A filter changes live delivery, not authorization or durable
history. The server MUST independently enforce Membership for every Group and MUST NOT reveal
whether an unauthorized Group exists.

One connection MAY interleave Events from multiple Groups. Sequence is guaranteed only within
each Group. A receiver MUST route by Group ID before applying sequence logic.

### 17.3 Flow control and liveness

`ACK` supplies durable progress. `PING` supplies liveness and MAY carry a Presence Record;
the peer echoes its nonce in a reply `PING`. Servers MUST apply bounded buffering and
per-Group backpressure. When a limit is reached they SHOULD pause that Group and emit
`BACKPRESSURE` with retry guidance rather than disconnecting unrelated Groups.

### 17.4 Canonical encoding

Wire JSON need not arrive in canonical member order, but every hash, identifier derived from
content, or signature MUST use RFC 8785 JCS bytes. Duplicate object member names MUST be
rejected before schema validation. Numbers not exactly representable by the implementation's
JCS pipeline MUST be rejected.

Large content is published as an Artifact and referenced by URI and content hash. Unknown
core properties are rejected by v0.1 schemas. Unknown noncritical Extension Profile data is
stored and relayed unchanged. Unknown critical extensions cause
`UNKNOWN_CRITICAL_EXTENSION`.

## 18. Extension Profiles

Developers MAY define custom Commands, Events, and data through Organization-approved
Extension Profiles. Each profile MUST declare a globally unique profile URI, semantic
version, schema URI and hash, required capabilities, criticality, and Organization approval
signature. A Group pins the supported major versions of profiles it uses.

Extension kinds MUST use the `ext.<organization>.<profile>.<name>` namespace defined by the
profile. An unknown noncritical extension MAY be retained and relayed without interpretation.
An Agent MUST refuse participation in a transition that depends on an unknown critical
profile.

An Extension Profile MUST NOT override or weaken identity, Membership, Event ordering,
idempotency, Session Epoch, Ownership Epoch, lease, budget, Approval, Artifact provenance,
Mission isolation, or the rule that Messages never authorize actions.

## 19. Errors

Errors MUST conform to `schemas/error.schema.json`. An error response MUST be machine-readable,
MUST state whether retry is safe, and SHOULD identify the related frame or Action ID without
exposing unauthorized data. Core codes are:

| Code | Meaning |
| --- | --- |
| `UNSUPPORTED_VERSION` | No compatible protocol version |
| `AUTH_REQUIRED` | Authentication is absent |
| `AUTH_INVALID_SIGNATURE` | A required signature failed |
| `AUTH_STALE_SESSION` | Session Epoch is fenced |
| `AUTH_STALE_COORDINATOR` | Coordinator Epoch is fenced |
| `AUTH_FORBIDDEN` | Actor lacks permission or policy eligibility |
| `GROUP_NOT_FOUND` | Group is absent or intentionally undisclosed |
| `MEMBERSHIP_REQUIRED` | No applicable Membership |
| `MEMBERSHIP_STALE` | Membership Epoch is fenced |
| `SCHEMA_VALIDATION_FAILED` | Object does not conform to its schema |
| `INVALID_COMMAND` | Command is well-formed but semantically invalid |
| `INVALID_STATE_TRANSITION` | Aggregate state forbids the transition |
| `REVISION_CONFLICT` | Expected revision does not match |
| `ACTION_ID_COLLISION` | Stable Action ID was reused with different content |
| `UNKNOWN_CRITICAL_EXTENSION` | Required extension cannot be interpreted |
| `WORK_CONTRACT_INCOMPLETE` | Required Work Contract information is missing |
| `WORK_OFFER_EXPIRED` | Offer is no longer valid |
| `WORK_ALREADY_OWNED` | Another candidate won exclusive ownership |
| `WORK_LEASE_EXPIRED` | Required lease is no longer valid |
| `WORK_STALE_OWNERSHIP` | Ownership Epoch is fenced |
| `APPROVAL_REQUIRED` | Policy gate has not been satisfied |
| `BUDGET_EXCEEDED` | A hard Mission or WorkItem budget is exhausted |
| `RATE_LIMITED` | Policy rate or recursion threshold was reached |
| `BACKPRESSURE` | Receiver cannot currently accept more traffic |
| `CURSOR_TOO_OLD` | Online replay no longer contains the requested position |
| `PROTOCOL_VIOLATION` | Peer violated framing or a core invariant |
| `INTERNAL_ERROR` | Authority failed without accepting the transition |

Retries MUST retain the original Action ID and signed content unless the error explicitly
requires a revised Command. `ACTION_ID_COLLISION`, invalid signature, and stale fencing errors
are not retryable without creating or obtaining new authoritative state.

## 20. Rate, recursion, and runaway controls

Organization policy MUST support limits on Message and proposal rates, unresolved
clarification rounds, active and queued WorkItems, delegation depth, token/time/financial
budgets, and circular or duplicate decomposition. These controls SHOULD use soft thresholds,
Coordinator notification, and explicit escalation rather than fixed low protocol ceilings.

An implementation MUST reject cyclic delegation or Mission ancestry. When legitimate work
requires more depth, budget, or rate, the Coordinator may request policy or MissionOwner
approval and continue after the grant. Policy limits MUST NOT silently discard accepted work.

A cooperation-limit escalation MUST be represented by a durable, one-shot **Cooperation
Override Grant**, not by an injected boolean, local callback result, or reusable exemption. The
grant MUST bind one Mission, Group, policy name, beneficiary Principal, target Command kind,
target Action ID, reason, approver, grant time, and expiry. Only the MissionOwner or an authorized
Organization policy actor may issue it. The target Command MUST cite the grant ID in its
`cooperationOverrideGrantId` envelope member.

Before accepting the target transition, Group Authority MUST verify that the cited grant exists,
is unexpired and unconsumed, and exactly matches the Command's Mission, Group, actor, kind, Action
ID, and exceeded policy. It MUST atomically consume the grant only when the target transition is
accepted. Both issuance and consumption MUST be appended to the authoritative Policy Log, with
consumption linked to the accepted Event. An idempotent retry of the same accepted Command returns
its prior Event; any other attempted use of the grant MUST fail.

## 21. Schema and version compatibility

All v0.1 schemas use JSON Schema Draft 2020-12. Core objects set
`additionalProperties: false`; extensibility occurs only through explicit `extensions`
members and approved profiles. Implementations MUST preserve an unknown noncritical extension
byte-equivalently for canonical relay where possible.

The wire `protocolVersion` is `0.1`. A backward-compatible schema clarification increments
the specification patch version without changing the wire version. A change that alters core
semantics or required fields requires a new wire minor or major version and handshake
negotiation.

The 21 normative schemas are:

* `common.schema.json`
* `websocket-frame.schema.json`
* `command.schema.json`
* `event.schema.json`
* `agent-card.schema.json`
* `presence-record.schema.json`
* `mission.schema.json`
* `group.schema.json`
* `membership.schema.json`
* `conversation.schema.json` and `message.schema.json`
* `work-contract.schema.json` and `work-item.schema.json`
* `artifact.schema.json` and `evidence.schema.json`
* `lease.schema.json`
* `approval.schema.json`
* `context-package.schema.json`
* `group-snapshot.schema.json`
* `extension-profile.schema.json`
* `error.schema.json`

## 22. Conformance and required proof of concept

An implementation conforms to MissionWeaveProtocol 0.1 only if it:

* validates every durable object against the normative schemas;
* passes valid and invalid vectors in `conformance/vectors/`;
* enforces all Mission and WorkItem transitions;
* demonstrates replay, deduplication, optimistic concurrency, and fencing;
* demonstrates authorization and the Message/non-authority invariant; and
* passes failure-recovery tests without accepting stale or duplicate side effects.

Passing `missionweaveprotocol-conformance` or the repository's schema vectors demonstrates
schema-and-vector conformance only. It is necessary but not sufficient evidence of full protocol
conformance. A reference implementation MUST claim full MissionWeaveProtocol 0.1 conformance
only when automated positive and negative evidence covers every core Command and Event kind
above and every transition row in Sections 7.1 and 10.2; otherwise it MUST report the narrower
verified subset explicitly.

The v0.1 reference proof of concept MUST use Python and run two concurrent
software-development Missions with at least one shared Worker. At least one Mission MUST
exercise requirements analysis, implementation, testing, code review, integration, and human
Approval as separate graph stages. The proof of concept MUST demonstrate distinct per-Group
queues, global weighted-fair scheduling, context and credential isolation, multiple execution
slots, safe checkpoint preemption, Coordinator review, and a human Approval interface.

Its failure suite MUST inject duplicate Event delivery, Worker restart and queue rebuilding,
Coordinator failure and epoch replacement, temporary Group disconnection, lease expiry and
WorkItem reassignment, a high-priority arrival, and a human change request. The Python
implementation is a reference implementation, not the normative specification.

The proof of concept MUST remain within one Organization and one logical Group service. It
MUST NOT require federation, physical peer-to-peer routing, distributed consensus, Group
end-to-end encryption, or custom Extension Profiles to demonstrate core conformance.

## 23. Licensing

The specification, schemas, conformance suite, and reference implementation are licensed
under Apache License 2.0. The license does not grant trademark rights.
