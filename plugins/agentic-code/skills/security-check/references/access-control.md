# Access rules, roles, tenants and limits

Load this when the change touches database rules or policies, roles, membership, seats, invitations or a plan limit. The examples are an invented web shop.

## Rules that decide who may read and write
- **An open rule is the first thing to look for:** `allow read, write: if true`, a policy that returns true, row-level security switched off on a table, a rule that only checks that the caller is signed in. Signed in means "anyone who registered", which is anyone.
- **Ownership:** a document or row names its owner, and the rule compares the caller with it. Check both reads and writes; a readable table of orders leaks every customer's address even if writes are locked.
- **Tenant isolation:** in a multi-tenant product every document carries the tenant id, every rule compares it with the caller's tenant, and every query filters on it. A rule that looks fine for one document can still allow a list query across tenants.
- **Child collections and tables:** a rule on `shops/{id}` does not protect `shops/{id}/orders`. Each level needs its own rule, or an explicit inheritance you can point to.
- **Field-level write protection (the common miss):** if a user may update their own profile, they can also update `role`, `isAdmin`, `plan`, `seats` and `subscriptionActive` in it, unless the rule lists which fields may change. Check that those fields are written only by the server, or are compared old against new in the rule.
- **Where the role comes from:** a signed token claim set by the server, or a server-side lookup. Not a field in a document the caller can write, and not a value sent in the request.
- **Create is not update:** a rule that is safe for updates can be open for creates (the caller picks the owner, the role, the id).

## Roles and membership
- Who may invite, remove or change the role of whom? A member must not be able to promote themselves or demote an owner.
- The last owner cannot be removed or demoted, or the account is orphaned.
- A role change, a removed member or a revoked invitation must stop working on the server at once, not when the client next refreshes.

## Seats and subscription
- The seat limit and the plan are checked where the member is added, on the server, in the same transaction as the write. A check in the client, or one that reads then writes without a transaction, can be raced past the limit.
- A cached "subscription active" flag in a document the user can write is not a subscription check.

## Invitations and bearer tokens
- An invitation link or token is a credential. It is single use or expires, is stored hashed where practical, is never logged, and never returned to a client that is not its intended recipient (for example the member list must not include other people's pending tokens).

## Test every rule change
Against an emulator or a test database, with two users and two tenants:
- the owner can do the thing (allowed);
- another tenant's user cannot read it, write it or list it (denied);
- a member cannot change their own role or plan field (denied);
- an anonymous caller cannot do anything the rule does not name (denied).
A rule change without a denied case has not been tested.
