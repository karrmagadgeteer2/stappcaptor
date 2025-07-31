# stappcaptor
Streamlit app for Captor marketing

## Authenticating Against Captor

The GraphQL API requires a Bearer token obtained from
`https://auth.captor.se`. Tokens can be acquired either through the browser
callback flow or by making a direct `POST` request.

### Requesting a Token via `curl`

```bash
curl -X POST \
  'https://auth.captor.se/token' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=<user>&password=<pass>&client_id=prod'
```

The response includes an `access_token` which can be supplied to
`GraphqlClient`:

```python
from graphql_client import GraphqlClient

client = GraphqlClient()
client.login_with_credentials('username', 'password')
```

The token is stored in `~/.captor_streamlit` for subsequent runs.

### Logging in via the Streamlit App

If you launch the app without a token, a login form will ask for your username
and password. Submitting the form issues the same request as shown above and
prints the JSON response. The `access_token` field is then used for queries
during that session.
