"""durable() must survive several threads of one process writing the same file."""
import json,sys,tempfile,threading,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'hardware/daily-update'))
from prevention_guard import durable

class DurableThreads(unittest.TestCase):
    def test_concurrent_writers_never_fail_and_leave_one_valid_file(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'progress.private.json';errors=[]
            def work(n):
                try:
                    for i in range(150):durable(target,{'thread':n,'i':i})
                except Exception as error:errors.append(repr(error))
            threads=[threading.Thread(target=work,args=(n,)) for n in range(6)]
            for t in threads:t.start()
            for t in threads:t.join()
            self.assertEqual(errors,[])
            self.assertIn('thread',json.loads(target.read_text()))
            self.assertEqual([p.name for p in Path(d).iterdir()],['progress.private.json'])

if __name__=='__main__':unittest.main()
