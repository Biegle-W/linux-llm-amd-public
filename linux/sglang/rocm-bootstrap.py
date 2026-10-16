"""Start the isolated RDNA3 fork with AMD SMI initialized before torch."""
import amdsmi
if __name__ == '__main__':
    import runpy
    runpy.run_module('sglang.launch_server', run_name='__main__')
