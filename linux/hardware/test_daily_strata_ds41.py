"""Provisional DeepSeek installation restores its own component after failure."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dsh'))
spec=importlib.util.spec_from_file_location('daily_ds_test',ROOT/'hardware/daily-update/daily_update.py')
daily=importlib.util.module_from_spec(spec);spec.loader.exec_module(daily)


class Rollback(unittest.TestCase):
    def exercise(self,fail):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);src=base/'component/upstream';src.mkdir(parents=True)
            (src/'old-only').write_text('preserve original source and local state')
            pin=base/'component/runtime.json';pin.write_text(json.dumps({'source_commit':'old'}))
            profile=base/'profile.json';profile.write_text(json.dumps({'exe':str(src/'build-hip/strata-dsv41'),
                'args':[],'local_validation':{'status':'passed','source_commit':'old'}}))
            old_profile=profile.read_bytes();old_pin=pin.read_bytes()
            qwen=base/'qwen-sentinel';qwen.write_text('unchanged')
            stage=base/'stage';candidate=stage/'src/build-hip';candidate.mkdir(parents=True)
            (candidate/'strata-dsv41').write_bytes(b'candidate binary')
            (stage/'src/CMakeLists.txt').write_text('project(strata VERSION 0.1.49.1 LANGUAGES CXX)\n')
            engine=daily.StrataDeepSeek();engine.src=src;engine.pin=pin
            engine.profile_files=lambda:[profile]
            if fail:
                with patch.object(daily.shutil,'copytree',side_effect=OSError('interrupted copy')):
                    with self.assertRaises(OSError):engine.install(stage,'new',stage/'log')
            else:
                engine.install(stage,'new',stage/'log')
                self.assertEqual(json.loads(pin.read_text())['source_commit'],'new')
                self.assertEqual(json.loads(pin.read_text())['engine_version'],'0.1.49.1')
                self.assertEqual(json.loads(profile.read_text())['local_validation']['normal_integration_status'],'pending')
            engine.rollback(stage,stage/'log')
            engine.rollback(stage,stage/'log')
            self.assertTrue((src/'old-only').exists())
            self.assertEqual(profile.read_bytes(),old_profile)
            self.assertEqual(pin.read_bytes(),old_pin)
            self.assertEqual(qwen.read_text(),'unchanged')

    def test_completed_provisional_install_rolls_back(self):self.exercise(False)
    def test_partial_source_copy_rolls_back(self):self.exercise(True)


if __name__=='__main__':unittest.main()
