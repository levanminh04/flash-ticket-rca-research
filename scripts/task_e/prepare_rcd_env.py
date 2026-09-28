"""Explicit isolated comparator environment preparation after recorded resume."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import time
W=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(W))
from scripts.task_e.rcd_runtime import PINNED_PACKAGES,CUSTOM_FILES,verify_pinned_sources
from scripts.task_e.execution import require_contract,save_json,file_sha


def main():
    run=Path(sys.argv[1]); require_contract(run,'environment')
    gate=json.loads((W/'results/task-e/continuation-resume-receipt.json').read_text(encoding='utf-8'))
    if gate['status']!='AUTO_RESUME_AUTHORIZED_DEVELOPMENT_ONLY':
        raise RuntimeError('Resume gate not met')
    upstream,source=verify_pinned_sources(W)
    save_json(run/'source-verification.json',source)
    target=(W/'environments/task-e/rcd39').resolve()
    target.relative_to((W/'environments/task-e').resolve())
    py=target/'Scripts/python.exe'
    commands=[]
    def execute(args):
        start=time.perf_counter()
        print('Executing environment step '+str(len(commands)+1),flush=True)
        result=subprocess.run([str(a) for a in args],cwd=W)
        commands.append({'args':[str(a) for a in args],'exit_code':result.returncode,'seconds':time.perf_counter()-start})
        save_json(run/('command-'+str(len(commands))+'.json'),commands[-1])
        if result.returncode:
            raise RuntimeError('Environment command failed; preserve attempt')
    if not py.is_file():
        if target.exists():
            raise RuntimeError('Existing incomplete target; inspect before repair')
        execute(['C:/Users/84583/AppData/Local/Programs/Python/Python39/python.exe','-m','venv',target])
    execute([py,'-m','pip','install','pip==25.2','setuptools==68.2.2','wheel==0.41.3'])
    execute([py,'-m','pip','install','--report',run/'pip-install-report.json',*[k+'=='+v for k,v in PINNED_PACKAGES.items()]])
    customized=[]
    for relative in CUSTOM_FILES:
        src=upstream/'lib/causallearn'/relative
        dst=target/'Lib/site-packages/causallearn'/relative
        before=file_sha(dst)
        shutil.copyfile(src,dst)
        customized.append({'path':str(dst),'before_sha256':before,'source_sha256':file_sha(src),'installed_sha256':file_sha(dst)})
    save_json(run/'customizations.json',customized)
    execute([py,'-m','pip','check'])
    freeze=subprocess.check_output([str(py),'-m','pip','freeze','--all'],text=True)
    (run/'freeze.txt').write_text(freeze,encoding='utf-8')
    version=subprocess.check_output([str(py),'--version'],text=True).strip()
    save_json(run/'environment-result.json',{'status':'PREPARED_NOT_YET_NUMERICALLY_QUALIFIED','python':version,'commands':commands,'pins':PINNED_PACKAGES})


if __name__=='__main__':main()
