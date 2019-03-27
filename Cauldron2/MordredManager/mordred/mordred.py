# import sys
import json
import tempfile
import os
import logging
import argparse

from sirmordred.config import Config
from sirmordred.task_collection import TaskRawDataCollection
from sirmordred.task_enrich import TaskEnrich
from sirmordred.task_projects import TaskProjects
from sirmordred.task_panels import TaskPanels, TaskPanelsMenu

logging.basicConfig(level=logging.INFO)

CONFIG_PATH = 'mordred/setup-default.cfg'
JSON_DIR_PATH = 'projects_json'
BACKEND_SECTIONS = ['git', 'github']  # add git


def run_mordred(repo, gh_token):
    projects_file = _create_projects_file(repo)
    cfg = _create_config(projects_file, gh_token)
    _get_raw(cfg)
    _get_enrich(cfg)
    # _get_panels(cfg)


def _create_projects_file(repo):
    """
    Check the source of the repository and create the projects.json for it
    :param repo: URL for the repository
    :return: Path for the projects.json
    """
    logging.info("Creating projects.json for %s", repo)
    if not os.path.isdir(JSON_DIR_PATH):
        try:
            os.mkdir(JSON_DIR_PATH)
        except OSError:
            logging.error("Creation of directory %s failed", JSON_DIR_PATH)
    # TODO: Check url
    projects = dict()
    projects['Project'] = dict()
    projects['Project']['git'] = list()
    projects['Project']['git'].append(repo + '.git')
    projects['Project']['github'] = list()
    projects['Project']['github'].append(repo)

    projects_file = tempfile.NamedTemporaryFile('w+',
                                                prefix='projects_',
                                                dir=JSON_DIR_PATH,
                                                delete=False)
    json.dump(projects, projects_file)

    return projects_file.name


def _create_config(projects_file, gh_token):
    cfg = Config(CONFIG_PATH)
    cfg.set_param('github', 'api-token', gh_token)
    cfg.set_param('projects', 'projects_file', projects_file)
    return cfg


def _get_raw(config):
    logging.info("Loading raw data...")
    for backend in BACKEND_SECTIONS:
        logging.info("Loading raw data for %s", backend)
        TaskProjects(config).execute()  # Basically get the projects and save them in the TaskProjects
        task = TaskRawDataCollection(config, backend_section=backend)
        try:
            task.execute()
            logging.info("Loading raw data for %s finished!", backend)
        except Exception as e:
            # TODO: More specific exception
            logging.warning("Error loading raw data from %s. Raising exception", backend)
            raise


def _get_enrich(config):
    logging.info("Enriching data...")
    for backend in BACKEND_SECTIONS:
        logging.info("Enriching data for %s", backend)
        TaskProjects(config).execute()
        task = TaskEnrich(config, backend_section=backend)
        try:
            task.execute()
            logging.info("Data for %s enriched!", backend)
        except Exception as e:
            # TODO: More specific exception
            logging.warning("Error enriching data for %s. Raising exception", backend)
            raise


def _get_panels(config):
    task = TaskPanels(config)
    task.execute()

    task = TaskPanelsMenu(config)
    task.execute()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run mordred for a repository")
    parser.add_argument('repo', help='repository to analyze')
    parser.add_argument('key', help='key for GitHub')
    args = parser.parse_args()
    run_mordred(args.repo, args.key)
