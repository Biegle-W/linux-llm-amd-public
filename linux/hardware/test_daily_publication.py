"""Exercise publication recovery against a local bare remote without inference."""
from pathlib import Path
import importlib.util,json,subprocess,tempfile,unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('daily_publication',ROOT/'hardware/daily-update/publish.py')
publication=importlib.util.module_from_spec(spec);spec.loader.exec_module(publication)

class PublicationRecovery(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.work=Path(self.temp.name);self.repo=self.work/'checkout';self.remote=self.work/'remote.git';self.log=self.work/'publish.private.log'
  self.git('init','--bare',str(self.remote),cwd=self.work)
  self.git('init','-b','main',str(self.repo),cwd=self.work)
  for key,value in [('user.name','Publication test'),('user.email','test@example.invalid')]:self.git('config',key,value)
  (self.repo/'intended').write_text('before\n');(self.repo/'unrelated').write_text('before\n')
  self.git('add','.');self.git('commit','-m','Initial');self.git('remote','add','origin',str(self.remote));self.git('push','origin','main')
 def git(self,*args,cwd=None):
  return subprocess.check_output(['git','-C',str(cwd or self.repo),*args],text=True,stderr=subprocess.STDOUT).strip()
 def test_failed_push_retries_owned_commit_without_duplicate_or_unrelated_stage(self):
  (self.repo/'intended').write_text('after\n');(self.repo/'unrelated').write_text('private pending work\n');self.git('add','unrelated')
  hook=self.remote/'hooks/pre-receive';hook.write_text('#!/bin/sh\nexit 1\n');hook.chmod(0o755)
  with self.assertRaises(subprocess.CalledProcessError):publication.commit(self.repo,['intended'],'Reviewed change',self.log)
  owned=self.git('rev-parse','HEAD');self.assertEqual(self.git('show','--format=','--name-only','HEAD'),'intended')
  self.assertEqual(self.git('diff','--cached','--name-only'),'unrelated')
  hook.write_text('#!/bin/sh\nexit 0\n')
  self.assertIn('pushed and verified',publication.commit(self.repo,['intended'],'Reviewed change',self.log))
  self.assertEqual(self.git('rev-parse','HEAD'),owned)
  self.assertEqual(self.git('ls-remote','origin','refs/heads/main').split()[0],owned)
  self.assertIn('nothing to commit',publication.commit(self.repo,['intended'],'Reviewed change',self.log))
 def test_unowned_ahead_commit_is_preserved_without_push(self):
  (self.repo/'intended').write_text('manual change\n');self.git('add','intended');self.git('commit','-m','Unreviewed local change');owned=self.git('rev-parse','HEAD')
  with self.assertRaisesRegex(RuntimeError,'not this queued publication'):publication.commit(self.repo,['intended'],'Publish',self.log)
  self.assertEqual(self.git('rev-parse','HEAD'),owned)
  self.assertNotEqual(self.git('ls-remote','origin','refs/heads/main').split()[0],owned)

if __name__=='__main__':unittest.main()
