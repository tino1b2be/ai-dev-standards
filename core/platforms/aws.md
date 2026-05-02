---
inclusion: always
---

# AWS platform standards

Conventions for how AWS itself is set up under a project: service choice,
account boundaries, identity, network posture, tagging, and cost controls.
These rules apply to any workload in the target stacks. They describe the
**platform**, not the **runtime** — Lambda packaging, cold-start behavior,
event-source wiring, and similar application-layer concerns live in
`core/application/aws-serverless.md`, not here.

## Service selection

- **Prefer managed services over self-hosted.** If AWS offers a managed
  service for a workload (queueing, pub/sub, key-value storage, workflows,
  auth), use it. Running Kafka, Redis, or Postgres on EC2 is a finding
  unless there is a documented reason the managed equivalent does not fit.
- **Serverless-first for compute.** Default to Lambda, Step Functions,
  API Gateway, EventBridge, SQS, SNS, and DynamoDB. Reach for ECS Fargate
  or EKS only when a workload's runtime shape (long-lived connections,
  >15 minute executions, heavy local state) makes serverless a bad fit.
- **No VMs as a first choice.** EC2 is a finding unless justified. If a
  workload lands on EC2, document why serverless and containers were
  rejected.
- **One service per responsibility.** Do not layer two services that do
  the same job (for example, SNS fan-out **and** EventBridge rules for the
  same event). Pick one and commit to it.

## Account structure

- **One AWS account per environment, per workload domain.** A project has
  separate accounts for `dev`, `staging`, and `prod`. Unrelated workload
  domains do not share an account with each other.
- **Never share a production account with non-production workloads.** No
  dev or staging resources run in the same account as prod. A blast radius
  that crosses environments is a finding.
- **Use AWS Organizations** to manage accounts. Enable `all-features` mode
  and apply service control policies (SCPs) at the OU level to enforce
  guardrails (deny region usage outside the approved list, deny root-user
  access keys, deny disabling CloudTrail).
- **Centralize billing** at the management account. Member accounts do not
  hold payment methods.
- **Isolate the security tooling account.** CloudTrail organization trail,
  Config aggregator, GuardDuty, and Security Hub land in a dedicated
  security account that only the security owners access.

## Identity and access

Deeper IAM patterns live here, not in the cross-cutting security file.

- **Humans use IAM Identity Center (SSO).** Do not create IAM users for
  people. If an existing IAM user for a human exists, migrate it to
  Identity Center and delete it.
- **Workloads use IAM roles.** Lambda functions, ECS tasks, Step Functions,
  EC2 instances, and CI jobs assume **their own role**, scoped to the
  actions and resources they touch. No shared machine role across unrelated
  workloads.
- **No long-lived access keys for humans.** If a human needs CLI access,
  it comes from Identity Center credentials, not `aws_access_key_id` in
  `~/.aws/credentials`. Long-lived keys for CI are allowed only when an
  OIDC federation path (for example, GitHub OIDC to an IAM role) is not
  available, and they are rotated on a schedule.
- **Permission boundaries** on every role a developer or pipeline can
  create. The boundary caps what any created role may ever do, so a
  mis-scoped policy cannot silently grant admin.
- **Condition keys** narrow every sensitive policy. At minimum use
  `aws:SourceAccount`, `aws:SourceArn`, `aws:PrincipalOrgID`, and
  `aws:RequestedRegion` where the action supports them. Policies without
  conditions on cross-account or cross-service access are a finding.
- **SCPs** at the organization or OU level enforce invariants the account
  cannot escape: deny root logins, deny disabling CloudTrail or Config,
  deny creating IAM users, deny regions outside the approved list.
- **Break-glass access** is a named, audited role with MFA required and
  alarms on every assumption. It is not a day-to-day login path.

## Region strategy

- **One primary region per workload**, chosen for latency to users and
  data residency requirements. All new resources default to that region.
- **Deny every other region** via SCP unless a workload explicitly opts
  in. A resource in an unexpected region is a finding.
- **Disaster recovery posture is documented**, not implicit. State the
  RPO and RTO per workload and the DR strategy that achieves it
  (pilot-light, warm-standby, active-active). A workload with no stated
  DR posture defaults to "single region, data loss possible on region
  failure" — and that default MUST be an explicit choice, not an
  oversight.
- **Data residency.** If the workload has regulatory residency
  requirements, pick the region accordingly and enforce it at the SCP
  layer. Do not rely on developers remembering.

## VPC and networking

- **Private subnets by default** for compute. Public subnets hold only
  load balancers, NAT gateways, and other edge components that must be
  reachable from the internet.
- **No public RDS, Aurora, ElastiCache, OpenSearch, or MSK.** These
  services live in private subnets with no public endpoint. Access is via
  VPC-internal clients, VPN, or AWS Client VPN — never an open security
  group.
- **VPC endpoints** (interface or gateway) for AWS service traffic that
  should not traverse the public internet: S3, DynamoDB, Secrets Manager,
  SSM, KMS, ECR, CloudWatch Logs. Keep service-to-service traffic on the
  AWS backbone.
- **Security groups are the primary access control.** Scope inbound rules
  to the specific security group or prefix list that needs access. Avoid
  `0.0.0.0/0` on anything except public-facing load balancers on `443`.
- **NACLs are a coarse fallback**, not the primary mechanism. Do not
  encode per-workload policy in NACLs.
- **No default VPC.** Delete the default VPC in every account and provision
  VPCs from infrastructure-as-code.

## Tagging

Every taggable resource MUST carry the following tags at creation time.
Untagged resources are a finding.

- `owner` — the team or individual accountable for the resource
  (`owner: team-REPLACE_ME`).
- `environment` — one of `dev`, `staging`, `prod`.
- `cost-center` — the billing allocation key (`cost-center: REPLACE_ME`).
- `service-name` — the logical service this resource belongs to
  (`service-name: REPLACE_ME`).

Rules:

- Tags are applied in infrastructure-as-code, not by hand in the console.
- An **AWS Organizations tag policy** enforces the required keys and their
  allowed values. A resource that violates the policy is flagged in AWS
  Config.
- Tag keys and values are lower-case `kebab-case`. No spaces, no mixed
  case.

## Cost awareness

- **Every account has an AWS Budget** with an alarm at 80% of its monthly
  expected spend and a second alarm at 100%. Alarms route to the account
  owner, not to a shared mailbox nobody reads.
- **Cost allocation tags** are activated for `owner`, `environment`,
  `cost-center`, and `service-name` so Cost Explorer can slice spend the
  same way the tagging policy requires.
- **Unused resources are cleaned up.** Orphaned EBS volumes, unattached
  Elastic IPs, idle NAT gateways, and empty load balancers are findings.
  A scheduled Config rule or cost-anomaly alarm catches them.
- **Developer sandboxes auto-expire.** Dev accounts or per-developer
  namespaces have a documented cleanup mechanism; resources older than
  the window are removed automatically.

## Auditability

- **CloudTrail organization trail** is enabled across every account and
  region, delivering to a centralized, immutable S3 bucket in the security
  account. Trails are never disabled locally — SCPs block that action.
- **AWS Config** is enabled in every account and region, with an
  organization aggregator in the security account.
- **GuardDuty** and **Security Hub** are enabled organization-wide, with
  findings aggregated to the security account.
- Disabling or tampering with any of the above is a finding and MUST
  trigger an alarm.
