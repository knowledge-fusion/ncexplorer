def test_wanderjoin_query():
    import sqlite3

    conn = sqlite3.connect("test.db")
    init = False
    if init:
        conn.execute(
            """CREATE TABLE KG
                 (
                 SOURCE        CHAR(50) NOT NULL,
                 TARGET        CHAR(50) NOT NULL);"""
        )
        conn.execute(
            """create unique index index_source_target on KG (SOURCE, TARGET);"""
        )

    insert = False
    if insert:
        conn.execute(
            """INSERT OR IGNORE INTO KG (SOURCE, TARGET)
              VALUES ('c', 'd'), ('a', 'b')"""
        )
    conn.commit()

    source = "'a', 'b', 'c'"
    destination = "'d'"

    query = f"SELECT * FROM KG hop1, KG hop2 WHERE hop1.target = hop2.source AND hop1.source IN ({source}) AND hop2.target IN ({destination})"
    cursor = conn.execute(query)
    for row in cursor:
        print(row)
