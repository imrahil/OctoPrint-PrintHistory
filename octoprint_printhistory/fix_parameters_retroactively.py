import os
from .parser import UniversalParser
import sqlite3
import json


def create_metadata_again(file_path, history_db):
    gcode_parser = UniversalParser(file_path, logger=None)
    file_name = file_path.split("/")[-1]
    parameters = json.dumps(gcode_parser.parse())
    conn = sqlite3.connect(history_db)
    cur = conn.cursor()
    cur.execute("UPDATE print_history SET parameters = ? WHERE fileName= ?", (parameters, file_name))
    conn.commit()
    conn.close()


def create_metadata_for_all(file_dir, history_db):
    files = os.listdir(file_dir)
    for file in files:
        print("fixing {}".format(file))
        create_metadata_again(os.path.join(file_dir, file), history_db)

