# Endpoints, payments, secrets, deployment and input

Load this when the change adds or changes a server endpoint, an export, a payment flow, a secret, a limit or a deployment setting.

## Endpoints and exports
- **Authenticate every call,** on the server, not in a client that "only shows the button to admins".
- **Authorise on the resource:** being signed in is not being allowed. The handler loads the resource and checks that this caller may touch this one. An `orderId` in the body is a request, not a fact.
- **Never trust values the body carries:** price, discount, role, owner id, tenant id, "isPaid". Read them from your own data.
- **Mass assignment:** do not spread a request body into a database write. List the fields that may be set.
- **A server-side request to a URL the user gave** (an import by link, a webhook target, an image fetch) can be pointed at your internal network or the cloud metadata address. Allow only known hosts, resolve the address and refuse private ranges, do not follow redirects blindly.
- **Exports** return only what the caller may see, with a size cap, and are logged.

## Limits on costly or abusable endpoints
Sign-in, password reset, e-mail sending, export and anything that calls a paid service (an AI model, an SMS) needs a limit enforced on the server, keyed on something the caller cannot reset (account, address), plus a daily ceiling on the total so a loop cannot run up a bill. A counter kept in the client or in a document the caller can write is not a limit. The key of a paid AI service never ships to the client; the client calls your endpoint, which checks the caller and the limit and then calls the service.

## Payments
- **The server computes the price** from its own catalogue. A price, currency or quantity sent by the client is a suggestion.
- **Verify the webhook's signature** with the provider's secret before acting on it, and handle repeated and out-of-order events.
- **Check the subscription state fresh** at the moment it matters (a cancelled plan, a failed renewal), not from a flag written at sign-up.
- Granting the product happens from the verified server event, never from the client saying "payment succeeded".

## Secrets
- A secret in the code, a commit, a log, a notes file or a client bundle is exposed. In a client build, anything that reaches the bundle (variables with a public prefix, constants) is public.
- If one has leaked, **rotate it.** Removing it from the history does not help: it was already copied.
- Secrets come from the environment or a secret store, `.env` files are ignored by git, and different environments have different secrets.

## Input and output
- Build queries with parameters, never by joining strings. Watch raw-query escape hatches in an ORM.
- Encode output for where it lands (HTML, attribute, URL, shell, a log line). Text from an AI model or another user is untrusted output.
- Uploads: check the size and the real type, store them outside the web root or on a storage service with its own rules, and never execute or serve them with a guessed type.

## Deployment
- Debug mode and verbose errors off in production; stack traces do not reach the user.
- CORS lists the origins you mean, not `*` with credentials.
- Source maps do not carry secrets or are not published; the `.git` folder is not served.
- Security headers set (content security policy, frame options, content-type options, transport security).
