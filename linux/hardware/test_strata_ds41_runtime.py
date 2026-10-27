"""Admission rejects settings which invalidate the dedicated DeepSeek proof."""
import copy
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dsh'))
from strata_ds41_runtime import check_settings


class Settings(unittest.TestCase):
    def setUp(self):
        self.cfg={'arch':'deepseek41','backend':'hip','gpu':[0,1],'parallel':1,
            'args':['--max-context','32768','--cpu-threads','24','--tp','2','--reserve-mib','8192','--ssd-cache','0','--dspark','on'],
            'installer':{'quant':'Maya-XS'},'env':{'STRATA_DS4_PROMPT_SKIP':'0','DS4_YOCO':'0','STRATA_DS4_SLOT_KEEP':'0'},
            'worker_swap_max_bytes':None,'startup_free_vram_gib':6}

    def test_retained_s_and_xs_choices(self):
        check_settings(self.cfg)
        self.cfg['installer']['quant']='Maya-S';self.cfg['args'][-1]='none'
        check_settings(self.cfg)

    def test_no_single_card_or_approximate_prompt_path(self):
        for change in ('single_gpu','prompt_skip','yoco','slots','expert_skip','reserve','swap','startup','context','wrong_drafter','unbounded_ram_store'):
            with self.subTest(change=change):
                c=copy.deepcopy(self.cfg)
                if change=='single_gpu':c['gpu']=[0]
                elif change=='prompt_skip':c['env']['STRATA_DS4_PROMPT_SKIP']='1'
                elif change=='yoco':c['env']['DS4_YOCO']='2'
                elif change=='slots':c['env']['STRATA_DS4_SLOT_KEEP']='1'
                elif change=='expert_skip':c['env']['STRATA_DS4_DISK_SKIP_W']='0.01'
                elif change=='swap':c['worker_swap_max_bytes']=1
                elif change=='startup':c['startup_free_vram_gib']=5
                elif change=='wrong_drafter':c['args'][-1]='none'
                elif change=='reserve':c['args'][c['args'].index('--reserve-mib')+1]='4096'
                elif change=='context':c['args'][c['args'].index('--max-context')+1]='65536'
                elif change=='unbounded_ram_store':c['args'][c['args'].index('--ssd-cache')+1]='999'
                with self.assertRaises(RuntimeError):check_settings(c)


if __name__=='__main__':unittest.main()
