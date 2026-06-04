import sqlite3

conn = sqlite3.connect(r'C:\Users\adity\Pictures\projects\InvenTree\_test\inventree.db')
c = conn.cursor()
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print('Tables:', [t[0] for t in tables])
c.execute('DROP TABLE IF EXISTS order_repairorder;')
c.execute('DROP TABLE IF EXISTS order_repairorderlineitem;')
c.execute('DROP TABLE IF EXISTS order_repairorderallocation;')
conn.commit()
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print('Tables after drop:', [t[0] for t in tables])
conn.close()
