# What the client may hold

Load this when the change is in a browser, mobile or desktop client and touches tokens, storage, links, keys or sign-in.

- **Assume everything in the client is readable:** the bundle, the local storage, the network traffic, a repackaged app. Hidden screens, disabled buttons and obfuscated names protect nothing.
- **No secret in the client build.** An API key with write power, a service account, a payment secret, an AI-service key: none of them. Variables a framework copies into the bundle by a public prefix are public by design. If a third-party key must be in the client, it is the restricted kind the provider designed for that, limited by app and domain.
- **Tokens in secure storage:** the platform's keychain or keystore on mobile; on the web an HTTP-only, secure, same-site cookie rather than plain `localStorage`, which any injected script can read. Plain preference files and unencrypted settings are not secure storage.
- **Decode is not verify:** reading a token's claims in the client to show a name is fine; trusting them for a decision is not. The server verifies the signature and the expiry.
- **Client checks are for the honest user:** limits, role gates, validation and "you have used 3 of 5 seats" are shown in the client and enforced on the server.
- **Links:** a deep link or a redirect parameter is input. Validate where it points (an allow-list), never pass its parameters straight into an action that changes data.
- **Biometric unlock** only unlocks a locally stored credential; it is not an authorisation for the server, and a bypass-able flag in storage is not a biometric check.
- **Output from a model or another user** is rendered as text, not as markup or script.
- **Logs and crash reports** carry no tokens, passwords or full personal data.
