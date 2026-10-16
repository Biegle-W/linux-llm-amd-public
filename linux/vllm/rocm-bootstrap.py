"""Preload AMD SMI before torch; retain multiprocessing's normal main guard."""
import amdsmi
if __name__ == '__main__':
    from vllm.entrypoints.cli.main import main
    main()
