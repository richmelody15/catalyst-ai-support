#!/usr/bin/env python3
"""Seed script: create the initial admin user.

Usage:
    python seed_admin.py
    # Or with custom credentials:
    ADMIN_EMAIL=me@example.com ADMIN_PASSWORD=secret python seed_admin.py
"""
import os
from database import SessionLocal, AdminUser, init_db

def main():
    init_db()
    db = SessionLocal()

    email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    password = os.environ.get("ADMIN_PASSWORD", "admin123")
    full_name = os.environ.get("ADMIN_FULL_NAME", "Super Admin")

    existing = db.query(AdminUser).filter_by(email=email).first()
    if existing:
        print(f"Admin user '{email}' already exists (id={existing.id}). Skipping.")
        db.close()
        return

    admin = AdminUser(email=email, full_name=full_name)
    admin.set_password(password)
    db.add(admin)
    db.commit()
    print(f"Admin user created: id={admin.id}, email={admin.email}")
    db.close()

if __name__ == "__main__":
    main()
