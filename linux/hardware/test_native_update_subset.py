"""A bounded tuning trial snapshots and changes only its requested native profile."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'dsh'),str(ROOT/'hardware/daily-update')]
import native_updates


class SelectedTrial(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'dsh').mkdir()
        self.source=self.root/'source';(self.source/'build-hip').mkdir(parents=True)
        (self.source/'build-hip/maya').write_bytes(b'candidate engine fixture')
        profiles={name:{'enabled':True,'config':name+'.json'} for name in ['glm','coder']}
        registry={'schema_version':1,'profiles':{name:{'status':'passed','family':'maya',
                 'binary_relative':'build-hip/maya','source_commit':'a'*40} for name in profiles}}
        (self.root/'dsh/maya-profiles.json').write_text(json.dumps(profiles))
        (self.root/'dsh/qualified-native-profiles.json').write_text(json.dumps(registry))
        for name in profiles:(self.root/'dsh'/f'{name}.json').write_text(json.dumps({'model_name':name,'args':[]}))
        self.stage=self.root/'trial';self.stage.mkdir()
        self.original={str(p):p.read_bytes() for p in (self.root/'dsh').glob('*.json')}
        self.patch=patch.object(native_updates,'ROOT',self.root);self.patch.start();self.addCleanup(self.patch.stop)

    def install(self,models):
        return native_updates.install('maya',self.stage,'b'*40,self.source,models=models)

    def test_selected_profile_only_changes_and_full_snapshot_restores(self):
        token=self.install(['glm']);data=json.loads((self.root/'dsh/qualified-native-profiles.json').read_text())
        self.assertEqual(data['profiles']['glm']['candidate_owner'],token)
        self.assertEqual(data['profiles']['coder']['status'],'passed')
        coder=str(self.root/'dsh/coder.json');self.assertEqual(Path(coder).read_bytes(),self.original[coder])
        native_updates.rollback(self.stage)
        self.assertEqual({p:Path(p).read_bytes() for p in self.original},self.original)

    def test_unknown_or_empty_subset_is_refused_without_mutation(self):
        for models in [[],['unknown'],['glm','unknown']]:
            with self.subTest(models=models),self.assertRaises(RuntimeError):self.install(models)
        self.assertFalse((self.stage/'native-rollback').exists())
        self.assertEqual({p:Path(p).read_bytes() for p in self.original},self.original)

    def test_default_still_selects_all_enabled_profiles(self):
        self.install(None)
        data=json.loads((self.root/'dsh/qualified-native-profiles.json').read_text())
        self.assertTrue(all(r['status']=='candidate' for r in data['profiles'].values()))


if __name__=='__main__':unittest.main()
