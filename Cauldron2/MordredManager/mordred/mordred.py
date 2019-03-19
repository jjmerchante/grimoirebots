# import sys
import json
import tempfile

from sirmordred.config import Config
from sirmordred.task_collection import TaskRawDataCollection
from sirmordred.task_enrich import TaskEnrich
from sirmordred.task_projects import TaskProjects
from sirmordred.task_panels import TaskPanels, TaskPanelsMenu


CONFIG_PATH = 'mordred/setup-default.cfg'
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
    print("Creating projects.json for", repo)
    # TODO: Check url
    projects = dict()
    projects['Test Project'] = dict()
    projects['Test Project']['git'] = list()
    projects['Test Project']['git'].append(repo + '.git')
    projects['Test Project']['github'] = list()
    projects['Test Project']['github'].append(repo)

    projects_file = tempfile.NamedTemporaryFile('w+',
                                                prefix='projects_',
                                                dir='./tmp_projects_json',
                                                delete=False)
    json.dump(projects, projects_file)

    return projects_file.name


def _create_config(projects_file, gh_token):
    cfg = Config(CONFIG_PATH)
    cfg.set_param('github', 'api-token', gh_token)
    cfg.set_param('projects', 'projects_file', projects_file)
    return cfg


def _get_raw(config):
    for backend in BACKEND_SECTIONS:
        TaskProjects(config).execute()  # Basically get the projects and save them in the TaskProjects
        task = TaskRawDataCollection(config, backend_section=backend)
        try:
            task.execute()
            print("Loading raw data finished!")
        except Exception as e:
            print("ERROR RAW", e)
            raise


def _get_enrich(config):
    for backend in BACKEND_SECTIONS:
        TaskProjects(config).execute()
        task = TaskEnrich(config, backend_section=backend)
        try:
            task.execute()
            print("Loading enriched data finished!")
        except Exception as e:
            print("ERROR ENRICH", e)
            raise


def _get_panels(config):
    task = TaskPanels(config)
    task.execute()

    task = TaskPanelsMenu(config)
    task.execute()

    print("Panels creation finished!")
