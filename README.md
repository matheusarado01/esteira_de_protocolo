# esteira_de_protocolo

This project relies on environment variables for configuration. Create a `.env` file in the repository root before running the application.

## Required variables

- `DB_HOST` – Database hostname
- `DB_PORT` – Database port
- `DB_NAME` – Database name
- `DB_USER` – Database user
- `DB_PASS` – Database password

Other features may use additional variables such as `IMAP_HOST`, `IMAP_USER`, `IMAP_PASS`, `OPENAI_API_KEY` and `SECRET_KEY`.

### Example `.env`

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=esteira_protocolo
DB_USER=postgres
DB_PASS=secret

IMAP_HOST=imap.example.com
IMAP_USER=your_user
IMAP_PASS=your_pass
OPENAI_API_KEY=your_key
SECRET_KEY=some-secret
```

