import argparse

from app.auth import create_user, init_auth_store
from app.history_schema import init_history_store
from app.history_uploads import cleanup_expired_uploads


def main() -> None:
    parser = argparse.ArgumentParser(description="Menu Recipe Agent administration")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create-user", help="Create a bearer-token user")
    create_parser.add_argument("--name", required=True, help="Display name for the user")
    create_parser.add_argument(
        "--storage-quota-bytes",
        type=int,
        default=None,
        help="Optional per-user upload storage quota override",
    )
    cleanup_parser = subparsers.add_parser(
        "cleanup-uploads",
        help="Soft-delete expired upload history and remove stored files",
    )
    cleanup_parser.add_argument(
        "--retention-days",
        type=int,
        default=None,
        help="Override UPLOAD_RETENTION_DAYS for this cleanup run",
    )

    args = parser.parse_args()
    init_history_store()
    init_auth_store()

    if args.command == "create-user":
        user, token = create_user(args.name, args.storage_quota_bytes)
        print(f"Created user: {user.display_name}")
        print(f"Public ID: {user.public_id}")
        print(f"Bearer token: {token}")
        print("Store this token now. It is hashed in SQLite and cannot be retrieved later.")
    elif args.command == "cleanup-uploads":
        deleted_count = cleanup_expired_uploads(args.retention_days)
        print(f"Expired upload records deleted: {deleted_count}")


if __name__ == "__main__":
    main()
