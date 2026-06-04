"""Delete migrations."""
import sqlite3

conn = sqlite3.connect(r'C:\Users\adity\Pictures\projects\InvenTree\_test\inventree.db')
c = conn.cursor()
c.execute("DELETE FROM django_migrations WHERE app='order' AND name LIKE '0120%';")
conn.commit()
conn.close()
