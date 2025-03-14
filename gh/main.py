from github import Github as _Github, InputGitTreeElement
from dotenv import load_dotenv
from pathlib import Path
import base64
from nacl import encoding, public
import os
import subprocess
from gh.mods.helper import workflow_permissions_
import yaml

class Github:
    @staticmethod
    def auth():
        load_dotenv()
        return _Github(os.getenv('GITHUB_TOKEN'))

    @staticmethod
    def info():
        g = Github.auth()
        user = g.get_user()
        return user.name, user.login, user.public_repos

    class Repo:
        @staticmethod
        def ls(owner):
            g = Github.auth()
            owner = g.get_user(owner)
            return [repo.name for repo in owner.get_repos()]

        @staticmethod
        def new(owner, repo_name, desc='description', private=True):
            g = Github.auth()
            try:
                user = g.get_user()
                if owner == user.login:
                    return user.create_repo(name=repo_name, description=desc, private=private)
                else:
                    org = g.get_organization(owner)
                    return org.create_repo(name=repo_name, description=desc, private=private)
            except Exception as e:
                print(f"Error: {e}")

        @staticmethod
        def rm(owner, repo_name):
            g = Github.auth()
            repo = g.get_repo(f"{owner}/{repo_name}")
            repo.delete()

        class update:
            @staticmethod
            def name(owner, repo_name, new_name):
                g = Github.auth()
                repo = g.get_repo(f"{owner}/{repo_name}")
                repo.edit(name=new_name)

            @staticmethod
            def desc(owner, repo_name, new_desc):
                g = Github.auth()
                repo = g.get_repo(f"{owner}/{repo_name}")
                repo.edit(description=new_desc)

        class collect:
            @staticmethod
            def yml(owner, repo, relative_path):
                g = Github.auth()
                repo = g.get_repo(f"{owner}/{repo}")
                try:
                    contents = repo.get_contents(relative_path)
                    yaml_file_content = contents.decoded_content.decode('utf-8')
                    yaml_data = yaml.safe_load(yaml_file_content)
                    return yaml_data
                except Exception as e:
                    print(f"Error: {e}")
                    return None
            yaml = yml

        @staticmethod
        def push(owner, repo_name, path='', branch='main'):
            g = Github.auth()
            repo = g.get_repo(f"{owner}/{repo_name}")
            clone_url = repo.ssh_url
            default_branch = repo.default_branch

            temp_dir = '/tmp/repo_clone'
            os.makedirs(temp_dir, exist_ok=True)

            result = subprocess.run(
                f'git clone -b {branch} {clone_url} {temp_dir}',
                shell=True,
                stderr=subprocess.PIPE
            )

            if result.returncode != 0:
                os.chdir(temp_dir)
                subprocess.run('git init', shell=True)
                subprocess.run(f'git remote add origin {clone_url}', shell=True)

                Path(f'{temp_dir}/README.md').write_text("# Initial Commit")
                subprocess.run('git add README.md', shell=True)
                subprocess.run('git commit -m "Initial commit"', shell=True)
                subprocess.run(f'git branch -M {branch}', shell=True)
                subprocess.run(f'git push -u origin {branch}', shell=True)

            if not os.path.exists(os.path.join(temp_dir, '.git')):
                raise Exception("Failed to initialize the repository.")

            src_path = Path(path)
            dst_path = Path(temp_dir)
            for item in src_path.rglob('*'):
                if item.is_file():
                    relative_path = item.relative_to(src_path)
                    target_path = dst_path / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    target_path.write_bytes(item.read_bytes())

            os.chdir(temp_dir)
            subprocess.run('git add .', shell=True)
            subprocess.run('git commit -m "Automated commit"', shell=True)
            subprocess.run(f'git push origin {branch}', shell=True)

        class rules:
            @staticmethod
            def import_rules(owner, repo_name, path='/path/to/rules.json'):
                # This would depend on what "importing rules" means for your use case
                pass

        class workflow:
            class permission:
                @staticmethod
                def read(owner, repo_name):
                    workflow_permissions_(owner, repo_name, 'read')

                @staticmethod
                def write(owner, repo_name):
                    workflow_permissions_(owner, repo_name, 'write')

            class secrets:
                @staticmethod
                def public_key(owner, repo_name):
                    token = os.getenv('GITHUB_TOKEN')
                    url = f"https://api.github.com/repos/{owner}/{repo_name}/actions/secrets/public-key"
                    headers = {
                        "Authorization": f"token {token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                    return response.json()

                @staticmethod
                def encrypt(public_key, secret_value):
                    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
                    sealed_box = public.SealedBox(public_key)
                    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
                    return base64.b64encode(encrypted).decode("utf-8")

                @staticmethod
                def new(owner, repo_name, label, value):
                    pub_key = Github.Repo.workflow.secrets.public_key(owner, repo_name)
                    key_id = pub_key['key_id']
                    encrypted_value = Github.Repo.workflow.secrets.encrypt(pub_key['key'], value)

                    token = os.getenv('GITHUB_TOKEN')
                    url = f"https://api.github.com/repos/{owner}/{repo_name}/actions/secrets/{label}"
                    headers = {
                        "Authorization": f"token {token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                    data = {
                        "encrypted_value": encrypted_value,
                        "key_id": key_id
                    }
                    response = requests.put(url, headers=headers, json=data)
                    response.raise_for_status()

    R = Repo
    repo = Repo

    class Org:
        @staticmethod
        def info(org_name):
            g = Github.auth()
            org = g.get_organization(org_name)
            return {'name': org.name, 'desc': org.description}

        @staticmethod
        def ls():
            g = Github.auth()
            return [org.login for org in g.get_user().get_orgs()]

        class update:
            @staticmethod
            def desc(org_name, new_desc):
                g = Github.auth()
                org = g.get_organization(org_name)
                org.edit(description=new_desc)
    O = Org
    org = Org
