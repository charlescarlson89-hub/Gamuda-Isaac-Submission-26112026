# View user IDs in Swagger

The read-only `GET /api/admin/users` endpoint lists account IDs and usernames,
including seeded demo accounts. It returns no password, session, contact,
location or wallet fields. It uses the same PostgreSQL database as FastAPI.

## Use it on this laptop

1. Log in with **Carlson** at http://127.0.0.1:5173/#/login.
2. In the same browser, open http://127.0.0.1:8001/docs.
3. Find **Admin → GET /api/admin/users**.
4. Choose **Try it out**, keep `limit=50` and `offset=0`, then **Execute**.
5. Read `users`, `total` and `has_more` in **Response body**.

Use the same hostname (`127.0.0.1`) for the frontend and Swagger so the browser
sends the existing session cookie. No token needs to be copied into Swagger.

- **401:** Log in first, or renew an expired session.
- **403:** The signed-in account is not an authorised administrator.
- **422:** Use a limit of 1–100 and an offset of zero or greater.

For the next page, increase `offset` by `limit` while `has_more` is true.
For example, `limit=50&offset=50` requests the second page.

## Configure administrators

Admin access is disabled by default. The server operator sets `ADMIN_USER_IDS`
in the private `%LOCALAPPDATA%/SoilSyncRemake/.env` file, then restarts FastAPI.
Carlson's verified local account, ID 26, has been enabled on this laptop.

```dotenv
# Example for the verified local database only:
ADMIN_USER_IDS=[26]
```

Check each account's identity in the target database before configuring IDs.
IDs can belong to different people in another database; review the allowlist
when changing `DATABASE_URL`. Never enable demo accounts as administrators.
An empty list (`[]`) disables access. Regular registration and profile updates
cannot change this server-side allowlist. There is no public route to grant
admin privileges or to create, edit or delete users through this directory.

## Forgotten password (local operator recovery)

In an interactive terminal at the project root, run:

```powershell
npm run account:reset -- --user-id 26
```

Verify the displayed username, then enter a new password twice. Input is hidden;
do not put the password into the command, chat or an environment file. The command
uses the configured database and requires the local operator's database access.
It stores an Argon2 hash, revokes that account's previous sessions and preserves
its progress and admin allowlist entry. Log in again with the new password.

This is a local recovery command, not a public forgot-password API. Other user
IDs must be checked against the intended account in the target database first.
