#!/usr/bin/env python3
"""CPU-only contracts for text-only H3 routing, preallocation checks and installation.

Uses lightweight stand-ins for Comfy/torch so no runtime import or GPU probe occurs.
Run: python3 graphics/test-h3-projected-loader.py
"""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parent

class Base:
    def clone(self):
        return Base()

class Projected:
    def __init__(self, base, projection):
        self._base, self._proj_name = base, projection
    def tokenize(self, text, **kwargs):
        return text, kwargs

class Contracts(unittest.TestCase):
    def setUp(self):
        self.allocations = []
        self.projection = {'W': types.SimpleNamespace(shape=[4096, 5120]), 'tap': 24, 'sink_out': object()}
        self.arch = ('boogu', '8B')
        def load(**kwargs):
            self.allocations.append(kwargs)
            return Base()
        paths = types.SimpleNamespace(get_full_path_or_raise=lambda *a: '8b.safetensors', get_folder_paths=lambda *a: [])
        self.ns = dict(ProjectedCLIP=Projected, folder_paths=paths, h3_projection_names=lambda: [], detect_arch=lambda p: self.arch,
                       gpu_device=lambda d: d, torch=types.SimpleNamespace(device=lambda d: d),
                       comfy=types.SimpleNamespace(sd=types.SimpleNamespace(load_clip=load, CLIPType=types.SimpleNamespace(BOOGU='boogu'))),
                       clipproj_projection=types.SimpleNamespace(load_projection=lambda p: self.projection))
        source = ROOT/'comfyui-device-loaders/__init__.py'
        tree = ast.parse(source.read_text())
        classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name in ('H3TextOnlyProjectedCLIP', 'GraphicsH3ProjectedCLIPLoader')]
        exec(compile(ast.Module(body=classes, type_ignores=[]), str(source), 'exec'), self.ns)
        self.clip = self.ns['H3TextOnlyProjectedCLIP'](Base(), 'ridge.safetensors')
        self.loader = self.ns['GraphicsH3ProjectedCLIPLoader']()

    def test_text_and_clone(self):
        for clip in (self.clip, self.clip.clone()):
            self.assertIs(type(clip), type(self.clip))
            self.assertEqual(clip.tokenize('hello')[1]['images'], [])

    def test_images_and_refs_rejected_including_clone(self):
        for clip in (self.clip, self.clip.clone()):
            for inputs in ({'images': [object()]}, {'minimax_ref_items': [object()]}):
                with self.assertRaisesRegex(ValueError, 'Native32B'):
                    clip.tokenize('hello', **inputs)

    def test_projection_rejected_before_allocation(self):
        for bad in ({'tap': 24, 'sink_out': object()}, {'W': types.SimpleNamespace(shape=[2560, 5120]), 'tap': 24, 'sink_out': object()},
                    {'W': types.SimpleNamespace(shape=[4096, 5120]), 'tap': 23, 'sink_out': object()},
                    {'W': types.SimpleNamespace(shape=[4096, 5120]), 'tap': 24}):
            self.projection = bad
            with self.assertRaises(ValueError):
                self.loader.load_clip('8b', 'ridge', 'cuda:1')
            self.assertEqual(self.allocations, [])

    def test_architecture_rejected_before_allocation(self):
        self.arch = ('minimax', '32B')
        with self.assertRaises(ValueError):
            self.loader.load_clip('32b', 'ridge', 'cuda:1')
        self.assertEqual(self.allocations, [])

    def test_initial_and_load_device(self):
        self.loader.load_clip('8b', 'ridge', 'cuda:1')
        options = self.allocations[0]['model_options']
        self.assertEqual(options, {'load_device': 'cuda:1', 'initial_device': 'cuda:1', 'offload_device': 'cpu'})

    def test_graphs_and_native_fallback(self):
        w = ROOT/'workflows'
        old = json.loads((w/'minimax-h3-native32b-api.json').read_text())
        new = json.loads((w/'minimax-h3-base-api.json').read_text())
        self.assertEqual({k:v for k,v in old.items() if k != '3'}, {k:v for k,v in new.items() if k != '3'})
        oldgui = json.loads((w/'minimax-h3-native32b.json').read_text())
        gui = json.loads((w/'minimax-h3-base.json').read_text())
        self.assertEqual(oldgui['links'], gui['links'])
        self.assertEqual([n for n in oldgui['nodes'] if n['id'] not in (3,100)], [n for n in gui['nodes'] if n['id'] not in (3,100)])
        encoder = next(n for n in gui['nodes'] if n['id'] == 3)
        self.assertEqual(encoder['type'], new['3']['class_type'])
        self.assertEqual(encoder['widgets_values'], [new['3']['inputs'][k] for k in ('clip_name','projection_name','device')])
        self.assertEqual(hashlib.sha256((w/'minimax-h3-native32b-api.json').read_bytes()).hexdigest(), '4e1ffa45df0aa5e6c80f24a2362d8ecfb122ddda9d65f4b4b969ed1ef895769b')
        self.assertEqual(hashlib.sha256((w/'minimax-h3-native32b.json').read_bytes()).hexdigest(), '64f2fde78e8e4280365d5774d77226766b61a7e72ebb6ef6740e08a60066f3e5')

    def test_vendor_identity_and_installer(self):
        vendor = ROOT/'comfyui-device-loaders/clipproj_vendor'
        provenance = json.loads((vendor/'SOURCE.json').read_text())
        for name, expected in provenance['files_sha256'].items():
            self.assertEqual(hashlib.sha256((vendor/name).read_bytes()).hexdigest(), expected)
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, str(ROOT/'install-device-loaders.py'), '--runtime', directory], check=True, capture_output=True)
            target = Path(directory)/'custom_nodes/local_graphics_devices'
            for name in ('__init__.py', *(f'clipproj_vendor/{n}' for n in ('__init__.py','clipproj_nodes.py','clipproj_projection.py','clipproj_pinning.py','LICENSE','SOURCE.json'))):
                self.assertEqual((target/name).read_bytes(), (ROOT/'comfyui-device-loaders'/name).read_bytes())

if __name__ == '__main__':
    unittest.main()
