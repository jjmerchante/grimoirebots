import sqlite3
import time
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
        waiting_msg = True
        while True:
            if waiting_msg is True:
                logging.info('Waiting for new repositories...')
                waiting_msg = False

            q = "SELECT id, url_gh, url_git, gh_token_id " \
                "FROM CauldronApp_repository " \
                "WHERE status = 'PENDING' " \
                "ORDER BY last_modified;"
            row = self._db_select(q)
            if row is not None:
                id_repo = row[0]
                url_gh = row[1]
                url_git = row[2]
                id_user = row[3]
                logging.info("Analyzing %s", url_gh)

                q = "SELECT token " \
                    "FROM CauldronApp_githubuser " \
                    "WHERE id = {};".format(id_user)
                row = self._db_select(q)
                token = row[0]

                q = "UPDATE CauldronApp_repository " \
                    "SET status = 'RUNNING' " \
                    "WHERE id='{}';".format(id_repo)
                self._db_update(q)

                # TODO: Timeout inside or outside. Or add workers
                with open('dashboards_logs/repository_{}.log'.format(id_repo), 'w') as f_log:
                    proc = subprocess.Popen(['python3', '-u', 'mordred/mordred.py', url_gh, url_git, token],
                                            stdout=f_log,
                                            stderr=subprocess.STDOUT)
                    proc.wait()
                    logging.info("Mordred analysis for {} finished with code: {}".format(url_gh, proc.returncode))

                if proc.returncode != 0:
                    logging.warning('An error occurred while analyzing %s' % url_gh)
                    q = "UPDATE CauldronApp_repository SET status = 'ERROR' WHERE id='{}';".format(id_repo)
                    self._db_update(q)
                else:
                    q = "UPDATE CauldronApp_repository SET status = 'COMPLETED' WHERE id='{}';".format(id_repo)
                    self._db_update(q)

                waiting_msg = True

            time.sleep(1)


if __name__ == "__main__":
    manager = MordredManager('../db.sqlite3')
    manager.run()
