import sqlite3
import time
from mordred.mordred import run_mordred
import logging
import subprocess

logging.basicConfig(level=logging.INFO)


class MordredManager:
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.cursor = self.conn.cursor()

    def _db_update(self, query):
        res = self.cursor.execute(query)
        self.conn.commit()
        return res

    def _db_select(self, query):
        res = self.cursor.execute(query)
        row = res.fetchone()
        return row

    def run(self):
        # TODO: More workers in case one of the analysis gets blocked
        waiting_msg = True
        while True:
            if waiting_msg is True:
                logging.info('Waiting for new repositories...')
                waiting_msg = False
            q = "SELECT id, url, gh_token_id FROM CauldronApp_task WHERE status = 'PENDING' ORDER BY last_modified;"
            row = self._db_select(q)
            if row is not None:
                id = row[0]
                url = row[1]
                id_user = row[2]
                logging.info("Analyzing %s", url)

                q = "SELECT token FROM CauldronApp_GithubToken WHERE id = {};".format(id_user)
                row = self._db_select(q)
                token = row[0]

                q = "UPDATE CauldronApp_task SET status = 'RUNNING' WHERE url='{}';".format(url)
                self._db_update(q)

                # TODO: Timeout inside or outside. Or add workers
                with open('dashboards_logs/dashboard_{}.log'.format(id), 'w') as f_log:
                    proc = subprocess.Popen(['python3', '-u', 'mordred/mordred.py', url, token],
                                            stdout=f_log,
                                            stderr=subprocess.STDOUT)
                    proc.wait()
                    logging.info("Mordred analysis for {} finished with code: {}".format(url, proc.returncode))

                if proc.returncode != 0:
                    logging.warning('An error ocurred while analyzing %s' % url)
                    q = "UPDATE CauldronApp_task SET status = 'ERROR' WHERE url='{}';".format(url)
                    self._db_update(q)
                else:
                    q = "UPDATE CauldronApp_task SET status = 'COMPLETED' WHERE url='{}';".format(url)
                    self._db_update(q)

                waiting_msg = True

            time.sleep(1)


if __name__ == "__main__":
    manager = MordredManager('../db.sqlite3')
    manager.run()
